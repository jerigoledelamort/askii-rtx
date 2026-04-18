#include <iostream>
#include <windows.h>
#include <d3d11.h>
#include <d3dcompiler.h>
#include <chrono>
#include <thread>

#include <imgui.h>
#include <imgui_impl_win32.h>
#include <imgui_impl_dx11.h>

#include "app_config.h"
#include "imgui_setup.h"
#include "ascii_renderer.h"
#include "config/default.h"

#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "d3dcompiler.lib")
#pragma comment(lib, "dxgi.lib")

using namespace gui;

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

	bool running_;

	// Управление
	glm::vec3 camera_vel_;
	float auto_rotate_angle_;

	static AsciiRtxGuiApp* s_instance_;

public:
	AsciiRtxGuiApp() 
		: renderer_(1280, 720), menu_(config_), hwnd_(nullptr),
		  d3d_device_(nullptr), d3d_context_(nullptr), swap_chain_(nullptr),
		  render_target_(nullptr), framebuffer_texture_(nullptr),
		  framebuffer_srv_(nullptr), running_(true),
		  camera_vel_(0.0f), auto_rotate_angle_(0.0f) {
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
		ImGuiIO& io = ImGui::GetIO();
		ImGui::StyleColorsDark();

		ImGui_ImplWin32_Init(hwnd_);
		ImGui_ImplDX11_Init(d3d_device_, d3d_context_);

		// Инициализация ASCII рендерера
		if (!renderer_.initialize()) {
			std::cerr << "[ERROR] ASCII renderer initialization failed\n";
			return false;
		}

		renderer_.resize(config_.window_width, config_.window_height);
		renderer_.set_char_size(config_.char_width, config_.char_height);

		// Загружаем конфиг по умолчанию
		try {
			config::init_default_config();
		} catch (...) {
			// Игнорируем ошибки
		}

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

				renderer_.resize(config_.window_width, config_.window_height);
			}
		}
	}

	void cleanup() {
		ImGui_ImplDX11_Shutdown();
		ImGui_ImplWin32_Shutdown();
		ImGui::DestroyContext();

		if (framebuffer_srv_) {
			framebuffer_srv_->Release();
			framebuffer_srv_ = nullptr;
		}
		if (framebuffer_texture_) {
			framebuffer_texture_->Release();
			framebuffer_texture_ = nullptr;
		}
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
		float speed = config_.camera_speed;

		switch (key) {
			case 'W': case 'w':
				camera_vel_.z += speed;
				break;
			case 'S': case 's':
				camera_vel_.z -= speed;
				break;
			case 'A': case 'a':
				camera_vel_.x -= speed;
				break;
			case 'D': case 'd':
				camera_vel_.x += speed;
				break;
			case 'Q': case 'q':
				camera_vel_.y -= speed;
				break;
			case 'E': case 'e':
				camera_vel_.y += speed;
				break;
			case 'R': case 'r':
				config_.camera_pos = glm::vec3(0.0f, 1.5f, 4.0f);
				config_.camera_rot = glm::vec3(0.0f);
				break;
			case VK_ESCAPE:
				running_ = false;
				PostQuitMessage(0);
				break;
		}
	}

	void handle_key_up(WPARAM key) {
		float speed = config_.camera_speed;

		switch (key) {
			case 'W': case 'w':
				camera_vel_.z -= speed;
				break;
			case 'S': case 's':
				camera_vel_.z += speed;
				break;
			case 'A': case 'a':
				camera_vel_.x += speed;
				break;
			case 'D': case 'd':
				camera_vel_.x -= speed;
				break;
			case 'Q': case 'q':
				camera_vel_.y += speed;
				break;
			case 'E': case 'e':
				camera_vel_.y -= speed;
				break;
		}
	}

	void update(float delta_time) {
		config_.camera_pos += camera_vel_ * delta_time;

		if (config_.auto_rotate) {
			auto_rotate_angle_ += config_.animation_speed * delta_time * 0.5f;
			config_.camera_rot.y = auto_rotate_angle_;
		}

		renderer_.set_char_size(config_.char_width, config_.char_height);
	}

	void render(float time) {
		// Рендеринг ASCII сцены
		renderer_.render_scene(time, config_.camera_pos, config_.camera_rot);

		// Очищаем экран
		float clear_color[4] = {0.0f, 0.0f, 0.0f, 1.0f};
		d3d_context_->ClearRenderTargetView(render_target_, clear_color);

		// Здесь можно вывести текстуру на экран
		// Для упрощения просто выводим ImGui

		ImGui_ImplDX11_NewFrame();
		ImGui_ImplWin32_NewFrame();
		ImGui::NewFrame();

		menu_.draw();

		// Покажем превью ASCII
		if (ImGui::Begin("ASCII Preview##main", nullptr, ImGuiWindowFlags_AlwaysAutoResize)) {
			ImGui::Text("Resolution: %dx%d", config_.window_width, config_.window_height);
			ImGui::Text("ASCII: %dx%d", config_.get_ascii_width(), config_.get_ascii_height());
			ImGui::Text("Char Size: %dx%d", config_.char_width, config_.char_height);
		}
		ImGui::End();

		ImGui::Render();
		ImGui_ImplDX11_RenderDrawData(ImGui::GetDrawData());

		swap_chain_->Present(config_.vsync ? 1 : 0, 0);
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

			auto now = std::chrono::high_resolution_clock::now();
			auto delta = std::chrono::duration_cast<std::chrono::milliseconds>(now - last_time).count();
			float delta_time = delta / 1000.0f;
			last_time = now;

			float current_time = std::chrono::duration_cast<std::chrono::seconds>(
				now.time_since_epoch()).count();

			update(delta_time);
			render(current_time);

			// Ограничение FPS (~60)
			if (delta < 16) {
				std::this_thread::sleep_for(std::chrono::milliseconds(16 - delta));
			}
		}
	}
};

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
