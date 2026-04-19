#include <iostream>
#include <algorithm>
#include <cmath>
#include <windows.h>
#include <d3d11.h>
#include <d3dcompiler.h>
#include <chrono>
#include <cstring>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include <imgui.h>
#include <imgui_impl_win32.h>
#include <imgui_impl_dx11.h>

#include "app_config.h"
#include "imgui_setup.h"
#include "ascii_renderer.h"
#include "config/default.h"
#include "engine/camera.h"

#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "d3dcompiler.lib")
#pragma comment(lib, "dxgi.lib")

using namespace gui;

namespace {

void debug_log(const std::string& message) {
	OutputDebugStringA((message + "\n").c_str());
	std::cout << message << '\n';
}

bool compile_hlsl_blob(
	const char* source,
	const char* entry,
	const char* target,
	ID3DBlob** out_blob
) {
	ID3DBlob* errors = nullptr;
	const UINT flags = D3DCOMPILE_ENABLE_STRICTNESS;
	const HRESULT hr = D3DCompile(
		source,
		strlen(source),
		nullptr,
		nullptr,
		nullptr,
		entry,
		target,
		flags,
		0,
		out_blob,
		&errors
	);
	if (FAILED(hr)) {
		if (errors) {
			debug_log(std::string(static_cast<const char*>(errors->GetBufferPointer())));
			errors->Release();
		}
		return false;
	}
	return true;
}

} // namespace

// Forward declaration
extern IMGUI_IMPL_API LRESULT ImGui_ImplWin32_WndProcHandler(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

LRESULT WINAPI WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

class AsciiRtxGuiApp {
private:
	AppConfig config_;
	AsciiRenderer renderer_;
	ImGuiMenu menu_;

	HWND hwnd_;
	ID3D11Device* d3d_device_;
	ID3D11DeviceContext* d3d_context_;
	IDXGISwapChain* swap_chain_;
	ID3D11RenderTargetView* render_target_;
	ID3D11Texture2D* framebuffer_texture_;
	ID3D11ShaderResourceView* framebuffer_srv_;
	int framebuffer_width_;
	int framebuffer_height_;

	// Полноэкранный блиц ASCII-текстуры в swapchain RTV
	ID3D11VertexShader* ascii_present_vs_ = nullptr;
	ID3D11PixelShader* ascii_present_ps_ = nullptr;
	ID3D11SamplerState* ascii_present_sampler_ = nullptr;

	bool running_;

	// Управление
	int frame_index_;
	std::vector<uint32_t> frame_pixels_;
	Camera view_camera_;

	// ЛКМ + дельта мыши (клиентские координаты)
	int prev_mouse_client_x_ = 0;
	int prev_mouse_client_y_ = 0;
	bool lmb_mouse_down_ = false;

	static AsciiRtxGuiApp* s_instance_;

	bool create_ascii_present_pass();
	void destroy_ascii_present_pass();
	void draw_ascii_fullscreen();

public:
	AsciiRtxGuiApp() 
		: renderer_(1280, 720), menu_(config_), hwnd_(nullptr),
		  d3d_device_(nullptr), d3d_context_(nullptr), swap_chain_(nullptr),
		  render_target_(nullptr), framebuffer_texture_(nullptr),
		  framebuffer_srv_(nullptr), framebuffer_width_(0), framebuffer_height_(0),
		  ascii_present_vs_(nullptr), ascii_present_ps_(nullptr), ascii_present_sampler_(nullptr),
		  running_(true),
		  frame_index_(0) {
		s_instance_ = this;
	}

	static LRESULT WINAPI static_wnd_proc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
		if (s_instance_) {
			return s_instance_->wnd_proc(hWnd, msg, wParam, lParam);
		}
		return DefWindowProc(hWnd, msg, wParam, lParam);
	}

	LRESULT wnd_proc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
		ImGui_ImplWin32_WndProcHandler(hWnd, msg, wParam, lParam);

		switch (msg) {
			case WM_DESTROY:
				PostQuitMessage(0);
				running_ = false;
				return 0;

			case WM_SIZE:
				if (d3d_device_ != nullptr && wParam != SIZE_MINIMIZED) {
					config_.window_width = LOWORD(lParam);
					config_.window_height = HIWORD(lParam);
					config_.sync_resolution_with_window();
					resize_buffers();
				}
				return 0;

			case WM_KEYDOWN:
				handle_key_down(wParam);
				break;

			case WM_KEYUP:
				handle_key_up(wParam);
				break;
		}

		return DefWindowProc(hWnd, msg, wParam, lParam);
	}

	bool initialize() {
		// Загружаем сохранённый конфиг
		config_.load_from_file("config.ini");

		// Создание окна
		WNDCLASSEX wc = {};
		wc.cbSize = sizeof(WNDCLASSEX);
		wc.style = CS_CLASSDC;
		wc.lpfnWndProc = static_wnd_proc;
		wc.hInstance = GetModuleHandle(nullptr);
		wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
		wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
		wc.lpszClassName = L"AsciiRtxGuiWindow";

		RegisterClassEx(&wc);

		DWORD style = WS_OVERLAPPEDWINDOW;
		if (config_.fullscreen) {
			style = WS_POPUP;
		}

		hwnd_ = CreateWindow(
			L"AsciiRtxGuiWindow",
			L"ASCII RTX v1 - GUI Application",
			style,
			0, 0,
			config_.window_width,
			config_.window_height,
			nullptr, nullptr,
			wc.hInstance,
			nullptr
		);

		if (!hwnd_) {
			std::cerr << "[ERROR] Window creation failed\n";
			return false;
		}

		// Создание Direct3D
		if (!create_d3d_device()) {
			std::cerr << "[ERROR] Direct3D device creation failed\n";
			DestroyWindow(hwnd_);
			return false;
		}

		// ImGui инициализация
		ImGui::CreateContext();
		ImGui::StyleColorsDark();
		{
			ImGuiIO& io = ImGui::GetIO();
			io.ConfigFlags &= ~ImGuiConfigFlags_NavEnableKeyboard;
		}

		ImGui_ImplWin32_Init(hwnd_);
		ImGui_ImplDX11_Init(d3d_device_, d3d_context_);

		if (!create_ascii_present_pass()) {
			std::cerr << "[ERROR] ASCII fullscreen present pass failed\n";
			return false;
		}

		// Инициализация ASCII рендерера
		if (!renderer_.initialize()) {
			std::cerr << "[ERROR] ASCII renderer initialization failed\n";
			return false;
		}

		try {
			config::init_default_config();
		} catch (...) {
		}

		config_.refresh_ascii_grid();
		apply_render_surface_from_config(true);

		view_camera_.sync_fps(
			config_.camera_pos,
			config_.camera_rot.x,
			config_.camera_rot.y
		);

		ShowWindow(hwnd_, SW_SHOW);
		UpdateWindow(hwnd_);

		std::cout << "[OK] Application initialized successfully\n";
		return true;
	}

	bool create_d3d_device() {
		DXGI_SWAP_CHAIN_DESC sd = {};
		sd.BufferCount = 1;
		sd.BufferDesc.Width = config_.window_width;
		sd.BufferDesc.Height = config_.window_height;
		sd.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
		sd.BufferDesc.RefreshRate.Numerator = 60;
		sd.BufferDesc.RefreshRate.Denominator = 1;
		sd.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
		sd.OutputWindow = hwnd_;
		sd.SampleDesc.Count = 1;
		sd.SampleDesc.Quality = 0;
		sd.Windowed = TRUE;
		sd.SwapEffect = DXGI_SWAP_EFFECT_DISCARD;

		D3D_FEATURE_LEVEL feature_level = D3D_FEATURE_LEVEL_11_0;

		if (FAILED(D3D11CreateDeviceAndSwapChain(
				nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, 0,
				&feature_level, 1, D3D11_SDK_VERSION,
				&sd, &swap_chain_, &d3d_device_, nullptr, &d3d_context_))) {
			return false;
		}

		// Создание render target
		ID3D11Texture2D* back_buffer = nullptr;
		if (FAILED(swap_chain_->GetBuffer(0, __uuidof(ID3D11Texture2D), (void**)&back_buffer))) {
			return false;
		}

		if (FAILED(d3d_device_->CreateRenderTargetView(back_buffer, nullptr, &render_target_))) {
			back_buffer->Release();
			return false;
		}

		back_buffer->Release();

		d3d_context_->OMSetRenderTargets(1, &render_target_, nullptr);

		// Viewport
		D3D11_VIEWPORT vp = {};
		vp.TopLeftX = 0;
		vp.TopLeftY = 0;
		vp.Width = (float)config_.window_width;
		vp.Height = (float)config_.window_height;
		vp.MinDepth = 0.0f;
		vp.MaxDepth = 1.0f;
		d3d_context_->RSSetViewports(1, &vp);

		return true;
	}

	void resize_buffers() {
		if (!swap_chain_ || !d3d_device_ || !d3d_context_) return;

		if (render_target_) {
			render_target_->Release();
			render_target_ = nullptr;
		}

		if (SUCCEEDED(swap_chain_->ResizeBuffers(1, config_.window_width, config_.window_height,
											   DXGI_FORMAT_R8G8B8A8_UNORM, 0))) {
			ID3D11Texture2D* back_buffer = nullptr;
			if (SUCCEEDED(swap_chain_->GetBuffer(0, __uuidof(ID3D11Texture2D), (void**)&back_buffer))) {
				d3d_device_->CreateRenderTargetView(back_buffer, nullptr, &render_target_);
				back_buffer->Release();

				d3d_context_->OMSetRenderTargets(1, &render_target_, nullptr);

				D3D11_VIEWPORT vp = {};
				vp.TopLeftX = 0;
				vp.TopLeftY = 0;
				vp.Width = (float)config_.window_width;
				vp.Height = (float)config_.window_height;
				vp.MinDepth = 0.0f;
				vp.MaxDepth = 1.0f;
				d3d_context_->RSSetViewports(1, &vp);

				apply_render_surface_from_config(true);
			}
		}
	}

	void cleanup() {
		ImGui_ImplDX11_Shutdown();
		ImGui_ImplWin32_Shutdown();
		ImGui::DestroyContext();

		destroy_ascii_present_pass();
		release_framebuffer_texture();
		if (render_target_) {
			render_target_->Release();
			render_target_ = nullptr;
		}
		if (d3d_context_) {
			d3d_context_->Release();
			d3d_context_ = nullptr;
		}
		if (swap_chain_) {
			swap_chain_->Release();
			swap_chain_ = nullptr;
		}
		if (d3d_device_) {
			d3d_device_->Release();
			d3d_device_ = nullptr;
		}

		if (hwnd_) {
			DestroyWindow(hwnd_);
			hwnd_ = nullptr;
		}

		config_.save_to_file("config.ini");
		std::cout << "[OK] Application cleanup complete\n";
	}

	void handle_key_down(WPARAM key) {
		switch (key) {
			case 'R': case 'r':
				config_.camera_pos = glm::vec3(0.0f, 1.5f, 4.0f);
				config_.camera_rot = glm::vec3(0.0f);
				view_camera_.sync_fps(
					config_.camera_pos,
					config_.camera_rot.x,
					config_.camera_rot.y
				);
				break;
			case VK_ESCAPE:
				running_ = false;
				PostQuitMessage(0);
				break;
		}
	}

	void handle_key_up(WPARAM /*key*/) {
	}

	void apply_render_surface_from_config(bool release_framebuffer) {
		config_.refresh_ascii_grid();
		renderer_.set_resolution(config_.resolution_width, config_.resolution_height);
		renderer_.set_ascii_grid(config_.ascii_width, config_.ascii_height);
		renderer_.set_char_size(config_.char_width, config_.char_height);
		renderer_.reset_accumulation_buffer();
		if (release_framebuffer) {
			release_framebuffer_texture();
		}
	}

	void fit_window_client_to_config() {
		if (!hwnd_) {
			return;
		}
		RECT rc = {0, 0, config_.window_width, config_.window_height};
		const DWORD style = static_cast<DWORD>(GetWindowLong(hwnd_, GWL_STYLE));
		const DWORD ex_style = static_cast<DWORD>(GetWindowLong(hwnd_, GWL_EXSTYLE));
		const BOOL has_menu = GetMenu(hwnd_) != nullptr;
		if (!AdjustWindowRectEx(&rc, style, has_menu, ex_style)) {
			return;
		}
		const int w = rc.right - rc.left;
		const int h = rc.bottom - rc.top;
		SetWindowPos(hwnd_, nullptr, 0, 0, w, h, SWP_NOMOVE | SWP_NOZORDER);
	}

	void sync_engine_from_config() {
		config::g_config.scene.num_objects = std::clamp(config_.num_objects, 1, 4);
	}

	void update(float delta_time) {
		if (config_.config_dirty) {
			apply_render_surface_from_config(true);
			fit_window_client_to_config();
			config_.config_dirty = false;
		}

		if (config_.camera_reset_requested) {
			config_.camera_pos = glm::vec3(0.0f, 1.5f, 4.0f);
			config_.camera_rot = glm::vec3(0.0f);
			view_camera_.sync_fps(
				config_.camera_pos,
				config_.camera_rot.x,
				config_.camera_rot.y
			);
			config_.camera_reset_requested = false;
		}

		sync_engine_from_config();

		view_camera_.set_move_speed(config_.camera_speed);
		view_camera_.set_rotate_sensitivity(config_.camera_rotate_speed * 0.18f);

		ImGuiIO& io = ImGui::GetIO();
		const bool mouse_blocked = io.WantCaptureMouse;
		// Зум по колесу, когда ImGui не захватывает мышь (AnyWindow почти всегда true из‑за меню/дока)
		const float wheel = io.MouseWheel;
		if (std::fabs(wheel) > 1e-6f && !mouse_blocked) {
			const float zoom_step = 2.5f * config_.camera_speed;
			view_camera_.dolly_view(wheel, zoom_step);
		}

		// Клавиатура: всегда опрос GetAsyncKeyState (не зависит от ImGui; не блокируем WASD)
		if ((GetAsyncKeyState('W') & 0x8000) != 0) {
			view_camera_.move_forward(delta_time);
		}
		if ((GetAsyncKeyState('S') & 0x8000) != 0) {
			view_camera_.move_backward(delta_time);
		}
		if ((GetAsyncKeyState('A') & 0x8000) != 0) {
			view_camera_.move_left(delta_time);
		}
		if ((GetAsyncKeyState('D') & 0x8000) != 0) {
			view_camera_.move_right(delta_time);
		}
		if ((GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0) {
			view_camera_.move_up(delta_time);
		}
		if ((GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0) {
			view_camera_.move_down(delta_time);
		}

		if (!mouse_blocked && hwnd_ != nullptr) {
			POINT cur{};
			if (GetCursorPos(&cur) && ScreenToClient(hwnd_, &cur) != FALSE) {
				const bool lmb = ((GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0);
				if (lmb) {
					if (lmb_mouse_down_) {
						const float dx = static_cast<float>(cur.x - prev_mouse_client_x_);
						const float dy = static_cast<float>(cur.y - prev_mouse_client_y_);
						view_camera_.rotate(dx, dy);
					}
					prev_mouse_client_x_ = cur.x;
					prev_mouse_client_y_ = cur.y;
					lmb_mouse_down_ = true;
				} else {
					lmb_mouse_down_ = false;
					prev_mouse_client_x_ = cur.x;
					prev_mouse_client_y_ = cur.y;
				}
			}
		}

		if (config_.auto_rotate) {
			view_camera_.add_yaw(config_.camera_rotate_speed * delta_time);
		}

		config_.camera_pos = view_camera_.get_position();
		config_.camera_rot.x = view_camera_.get_pitch();
		config_.camera_rot.y = view_camera_.get_yaw();

		renderer_.set_resolution(config_.resolution_width, config_.resolution_height);
		renderer_.set_ascii_grid(config_.ascii_width, config_.ascii_height);
		renderer_.set_char_size(config_.char_width, config_.char_height);
		renderer_.set_camera(config_.camera_pos, config_.camera_rot);

		if ((frame_index_ % 60) == 0) {
			std::ostringstream log;
			log << "[camera] position=(" << config_.camera_pos.x << ", " << config_.camera_pos.y
				<< ", " << config_.camera_pos.z << ") yaw=" << config_.camera_rot.y;
			debug_log(log.str());
		}
	}

	void release_framebuffer_texture() {
		if (framebuffer_srv_) {
			framebuffer_srv_->Release();
			framebuffer_srv_ = nullptr;
		}
		if (framebuffer_texture_) {
			framebuffer_texture_->Release();
			framebuffer_texture_ = nullptr;
		}
		framebuffer_width_ = 0;
		framebuffer_height_ = 0;
	}

	bool ensure_framebuffer_texture() {
		const int width = renderer_.get_width();
		const int height = renderer_.get_height();

		if (framebuffer_texture_ && framebuffer_srv_ &&
			framebuffer_width_ == width && framebuffer_height_ == height) {
			return true;
		}

		release_framebuffer_texture();

		D3D11_TEXTURE2D_DESC desc = {};
		desc.Width = width;
		desc.Height = height;
		desc.MipLevels = 1;
		desc.ArraySize = 1;
		desc.Format = DXGI_FORMAT_B8G8R8A8_UNORM;
		desc.SampleDesc.Count = 1;
		desc.Usage = D3D11_USAGE_DYNAMIC;
		desc.BindFlags = D3D11_BIND_SHADER_RESOURCE;
		desc.CPUAccessFlags = D3D11_CPU_ACCESS_WRITE;

		if (FAILED(d3d_device_->CreateTexture2D(&desc, nullptr, &framebuffer_texture_))) {
			debug_log("[render] failed to create framebuffer texture");
			return false;
		}

		D3D11_SHADER_RESOURCE_VIEW_DESC srv_desc = {};
		srv_desc.Format = desc.Format;
		srv_desc.ViewDimension = D3D11_SRV_DIMENSION_TEXTURE2D;
		srv_desc.Texture2D.MipLevels = 1;

		if (FAILED(d3d_device_->CreateShaderResourceView(framebuffer_texture_, &srv_desc, &framebuffer_srv_))) {
			debug_log("[render] failed to create framebuffer SRV");
			release_framebuffer_texture();
			return false;
		}

		framebuffer_width_ = width;
		framebuffer_height_ = height;
		return true;
	}

	bool update_framebuffer_texture() {
		if (!ensure_framebuffer_texture()) {
			return false;
		}

		if (frame_pixels_.empty()) {
			return false;
		}

		D3D11_MAPPED_SUBRESOURCE mapped = {};
		if (FAILED(d3d_context_->Map(framebuffer_texture_, 0, D3D11_MAP_WRITE_DISCARD, 0, &mapped))) {
			debug_log("[render] failed to map framebuffer texture");
			return false;
		}

		const size_t row_bytes = static_cast<size_t>(framebuffer_width_) * sizeof(uint32_t);
		const auto* src = reinterpret_cast<const unsigned char*>(frame_pixels_.data());
		auto* dst = reinterpret_cast<unsigned char*>(mapped.pData);

		for (int y = 0; y < framebuffer_height_; ++y) {
			std::memcpy(dst + static_cast<size_t>(y) * mapped.RowPitch,
				src + static_cast<size_t>(y) * row_bytes,
				row_bytes);
		}

		d3d_context_->Unmap(framebuffer_texture_, 0);
		return true;
	}

	void render(float time) {
		if ((frame_index_ % 60) == 0) {
			std::ostringstream log;
			log << "[render] frame=" << frame_index_ << " time=" << time;
			debug_log(log.str());
		}

		renderer_.render_scene(time * config_.animation_speed);
		renderer_.get_framebuffer(frame_pixels_);
		update_framebuffer_texture();

		if ((frame_index_ % 60) == 0) {
			size_t non_black_pixels = 0;
			for (uint32_t pixel : frame_pixels_) {
				if (pixel != 0xFF000000u) {
					++non_black_pixels;
				}
			}

			std::ostringstream log;
			log << "[render] visible_pixels=" << non_black_pixels << "/" << frame_pixels_.size();
			debug_log(log.str());
		}

		d3d_context_->OMSetRenderTargets(1, &render_target_, nullptr);
		D3D11_VIEWPORT vp = {};
		vp.TopLeftX = 0.0f;
		vp.TopLeftY = 0.0f;
		vp.Width = static_cast<float>(config_.window_width);
		vp.Height = static_cast<float>(config_.window_height);
		vp.MinDepth = 0.0f;
		vp.MaxDepth = 1.0f;
		d3d_context_->RSSetViewports(1, &vp);

		draw_ascii_fullscreen();

		ImGui_ImplDX11_NewFrame();
		ImGui_ImplWin32_NewFrame();
		ImGui::NewFrame();

		menu_.draw();

		ImGui::Render();
		ImGui_ImplDX11_RenderDrawData(ImGui::GetDrawData());

		if ((frame_index_ % 60) == 0) {
			debug_log("[render] presenting frame");
		}

		swap_chain_->Present(config_.vsync ? 1 : 0, 0);
		++frame_index_;
	}

	void run() {
		auto last_time = std::chrono::high_resolution_clock::now();

		std::cout << "\n╔════════════════════════════════════════════════════════════════╗\n";
		std::cout << "║            ASCII RTX v1 - GUI Interactive Application           ║\n";
		std::cout << "║              Real-time Visualization & Configuration            ║\n";
		std::cout << "╚════════════════════════════════════════════════════════════════╝\n\n";

		MSG msg = {};
		while (msg.message != WM_QUIT && running_) {
			if (PeekMessage(&msg, nullptr, 0U, 0U, PM_REMOVE)) {
				TranslateMessage(&msg);
				DispatchMessage(&msg);
				continue;
			}

			const auto now = std::chrono::high_resolution_clock::now();
			const auto frame_elapsed = now - last_time;
			last_time = now;

			using seconds_f = std::chrono::duration<float, std::ratio<1>>;
			float delta_time = std::chrono::duration_cast<seconds_f>(frame_elapsed).count();
			// Целые миллисекунды часто дают 0 на быстром цикле → WASD/Shift/Ctrl не двигают камеру
			if (delta_time < 1e-5f) {
				delta_time = 1.f / 240.f;
			}
			delta_time = std::min(delta_time, 0.25f);

			const auto elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(frame_elapsed).count();

			const float current_time = std::chrono::duration_cast<std::chrono::duration<float>>(
				now.time_since_epoch()).count();

			update(delta_time);
			render(current_time);

			// Ограничение FPS (~60)
			if (elapsed_ms < 16) {
				std::this_thread::sleep_for(std::chrono::milliseconds(16 - elapsed_ms));
			}
		}
	}
};

bool AsciiRtxGuiApp::create_ascii_present_pass() {
	static const char kHlsl[] = R"(
Texture2D sceneTex : register(t0);
SamplerState samp : register(s0);
struct PSIn {
	float4 pos : SV_POSITION;
	float2 uv : TEXCOORD0;
};
PSIn VSMain(uint vid : SV_VertexID) {
	PSIn o;
	o.uv = float2((vid << 1) & 2, vid & 2);
	o.pos = float4(o.uv * float2(2.0f, -2.0f) + float2(-1.0f, 1.0f), 0.0f, 1.0f);
	return o;
}
float4 PSMain(PSIn input) : SV_Target {
	return sceneTex.Sample(samp, input.uv);
}
)";

	ID3DBlob* vs_blob = nullptr;
	ID3DBlob* ps_blob = nullptr;
	if (!compile_hlsl_blob(kHlsl, "VSMain", "vs_5_0", &vs_blob) || !vs_blob) {
		return false;
	}
	if (!compile_hlsl_blob(kHlsl, "PSMain", "ps_5_0", &ps_blob) || !ps_blob) {
		vs_blob->Release();
		return false;
	}

	HRESULT hr = d3d_device_->CreateVertexShader(
		vs_blob->GetBufferPointer(),
		vs_blob->GetBufferSize(),
		nullptr,
		&ascii_present_vs_
	);
	if (FAILED(hr)) {
		vs_blob->Release();
		ps_blob->Release();
		return false;
	}

	hr = d3d_device_->CreatePixelShader(
		ps_blob->GetBufferPointer(),
		ps_blob->GetBufferSize(),
		nullptr,
		&ascii_present_ps_
	);
	vs_blob->Release();
	ps_blob->Release();
	if (FAILED(hr)) {
		destroy_ascii_present_pass();
		return false;
	}

	D3D11_SAMPLER_DESC samp_desc = {};
	samp_desc.Filter = D3D11_FILTER_MIN_MAG_MIP_LINEAR;
	samp_desc.AddressU = D3D11_TEXTURE_ADDRESS_CLAMP;
	samp_desc.AddressV = D3D11_TEXTURE_ADDRESS_CLAMP;
	samp_desc.AddressW = D3D11_TEXTURE_ADDRESS_CLAMP;
	samp_desc.ComparisonFunc = D3D11_COMPARISON_NEVER;
	samp_desc.MaxLOD = D3D11_FLOAT32_MAX;

	hr = d3d_device_->CreateSamplerState(&samp_desc, &ascii_present_sampler_);
	if (FAILED(hr)) {
		destroy_ascii_present_pass();
		return false;
	}

	return true;
}

void AsciiRtxGuiApp::destroy_ascii_present_pass() {
	if (ascii_present_sampler_) {
		ascii_present_sampler_->Release();
		ascii_present_sampler_ = nullptr;
	}
	if (ascii_present_ps_) {
		ascii_present_ps_->Release();
		ascii_present_ps_ = nullptr;
	}
	if (ascii_present_vs_) {
		ascii_present_vs_->Release();
		ascii_present_vs_ = nullptr;
	}
}

void AsciiRtxGuiApp::draw_ascii_fullscreen() {
	if (!ascii_present_vs_ || !ascii_present_ps_ || !ascii_present_sampler_ || !framebuffer_srv_) {
		const float clear_color[4] = {0.0f, 0.0f, 0.0f, 1.0f};
		if (render_target_) {
			d3d_context_->ClearRenderTargetView(render_target_, clear_color);
		}
		return;
	}

	d3d_context_->IASetInputLayout(nullptr);
	d3d_context_->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
	d3d_context_->IASetVertexBuffers(0, 0, nullptr, nullptr, nullptr);

	d3d_context_->VSSetShader(ascii_present_vs_, nullptr, 0);
	d3d_context_->PSSetShader(ascii_present_ps_, nullptr, 0);
	d3d_context_->PSSetSamplers(0, 1, &ascii_present_sampler_);
	d3d_context_->PSSetShaderResources(0, 1, &framebuffer_srv_);

	d3d_context_->OMSetBlendState(nullptr, nullptr, 0xFFFFFFFFu);
	d3d_context_->OMSetDepthStencilState(nullptr, 0);

	d3d_context_->Draw(3, 0);

	ID3D11ShaderResourceView* null_srv = nullptr;
	d3d_context_->PSSetShaderResources(0, 1, &null_srv);
}

AsciiRtxGuiApp* AsciiRtxGuiApp::s_instance_ = nullptr;

extern IMGUI_IMPL_API LRESULT ImGui_ImplWin32_WndProcHandler(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
	try {
		AsciiRtxGuiApp app;

		if (!app.initialize()) {
			std::cerr << "[ERROR] Application initialization failed\n";
			return 1;
		}

		app.run();
		app.cleanup();

		std::cout << "\n[INFO] Application closed successfully\n";
		return 0;
	}
	catch (const std::exception& e) {
		std::cerr << "[EXCEPTION] " << e.what() << "\n";
		return 1;
	}
}
