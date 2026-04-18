#include "imgui_setup.h"
#include <imgui.h>
#include <imgui_impl_win32.h>
#include <imgui_impl_dx11.h>
#include <sstream>

namespace gui {

bool ImGuiSetup::initialize(int width, int height) {
	// Контекст создаётся в main.cpp
	return true;
}

void ImGuiSetup::shutdown() {
	// Шутдаун в main.cpp
}

void ImGuiSetup::new_frame() {
	// Вызывается в main.cpp
}

void ImGuiSetup::render() {
	// Рендеринг в main.cpp
}

void ImGuiSetup::setup_style() {
	ImGui::StyleColorsDark();
	ImGuiStyle& style = ImGui::GetStyle();
	style.FrameRounding = 4.0f;
	style.GrabRounding = 4.0f;
}

void ImGuiSetup::setup_fonts() {
	ImGuiIO& io = ImGui::GetIO();
	io.Fonts->AddFontDefault();
}

void ImGuiMenu::draw() {
	draw_main_menu_bar();

	if (show_config_menu_) {
		draw_config_window();
	}

	if (show_stats_window_ && config_.show_stats) {
		draw_stats_window();
	}
}

void ImGuiMenu::draw_main_menu_bar() {
	if (ImGui::BeginMainMenuBar()) {
		if (ImGui::BeginMenu("File")) {
			if (ImGui::MenuItem("Save Config")) {
				config_.save_to_file("config.ini");
			}
			ImGui::Separator();
			if (ImGui::MenuItem("Exit")) {
				// Выход
			}
			ImGui::EndMenu();
		}

		if (ImGui::BeginMenu("View")) {
			ImGui::MenuItem("Configuration", nullptr, &show_config_menu_);
			ImGui::MenuItem("Statistics", nullptr, &show_stats_window_);
			ImGui::Separator();
			ImGui::MenuItem("Show Stats", nullptr, &config_.show_stats);
			ImGui::EndMenu();
		}

		if (ImGui::BeginMenu("Help")) {
			ImGui::TextWrapped("Controls:\nWASD - Move\nArrows - Rotate\nR - Reset\nESC - Exit");
			ImGui::EndMenu();
		}

		ImGui::EndMainMenuBar();
	}
}

void ImGuiMenu::draw_config_window() {
	if (ImGui::Begin("Configuration##main", &show_config_menu_, ImGuiWindowFlags_AlwaysAutoResize)) {
		// === VIDEO SETTINGS ===
		if (ImGui::CollapsingHeader("Video Settings", ImGuiTreeNodeFlags_DefaultOpen)) {
			static const int resolutions[][2] = {
				{800, 600}, {1024, 768}, {1280, 720}, 
				{1600, 900}, {1920, 1080}, {2560, 1440}
			};
			static int resolution_idx = 2;

			if (ImGui::BeginCombo("Resolution##combo", 
					(std::to_string(config_.window_width) + "x" + 
					 std::to_string(config_.window_height)).c_str())) {
				for (int i = 0; i < 6; i++) {
					bool is_selected = (resolution_idx == i);
					if (ImGui::Selectable(
							(std::to_string(resolutions[i][0]) + "x" + 
							 std::to_string(resolutions[i][1])).c_str(),
							is_selected)) {
						resolution_idx = i;
						config_.window_width = resolutions[i][0];
						config_.window_height = resolutions[i][1];
					}
					if (is_selected)
						ImGui::SetItemDefaultFocus();
				}
				ImGui::EndCombo();
			}

			ImGui::Checkbox("Fullscreen##check", &config_.fullscreen);
			ImGui::Checkbox("V-Sync##check", &config_.vsync);
		}

		// === ASCII SETTINGS ===
		if (ImGui::CollapsingHeader("ASCII Settings", ImGuiTreeNodeFlags_DefaultOpen)) {
			static const int char_sizes[][2] = {
				{8, 16}, {10, 20}, {12, 24}, {14, 28}, {16, 32}
			};
			static int char_size_idx = 2;

			if (ImGui::BeginCombo("Character Size##combo",
					(std::to_string(config_.char_width) + "x" + 
					 std::to_string(config_.char_height)).c_str())) {
				for (int i = 0; i < 5; i++) {
					bool is_selected = (char_size_idx == i);
					if (ImGui::Selectable(
							(std::to_string(char_sizes[i][0]) + "x" + 
							 std::to_string(char_sizes[i][1])).c_str(),
							is_selected)) {
						char_size_idx = i;
						config_.char_width = char_sizes[i][0];
						config_.char_height = char_sizes[i][1];
					}
					if (is_selected)
						ImGui::SetItemDefaultFocus();
				}
				ImGui::EndCombo();
			}

			ImGui::Text("ASCII Grid: %dx%d", 
					   config_.get_ascii_width(), 
					   config_.get_ascii_height());
		}

		// === CAMERA SETTINGS ===
		if (ImGui::CollapsingHeader("Camera Settings", ImGuiTreeNodeFlags_DefaultOpen)) {
			ImGui::SliderFloat("Move Speed##slider", &config_.camera_speed, 0.01f, 1.0f);
			ImGui::SliderFloat("Rotation Speed##slider", &config_.camera_rotate_speed, 0.01f, 0.5f);
			ImGui::Checkbox("Auto Rotate##check", &config_.auto_rotate);

			if (ImGui::Button("Reset Camera##button")) {
				config_.camera_pos = glm::vec3(0.0f, 1.5f, 4.0f);
				config_.camera_rot = glm::vec3(0.0f);
			}
		}

		// === SCENE SETTINGS ===
		if (ImGui::CollapsingHeader("Scene Settings", ImGuiTreeNodeFlags_DefaultOpen)) {
			ImGui::SliderFloat("Animation Speed##slider", &config_.animation_speed, 0.0f, 3.0f);
			ImGui::SliderInt("Number of Objects##slider", &config_.num_objects, 1, 10);
		}

		ImGui::End();
	}
}

void ImGuiMenu::draw_stats_window() {
	ImGuiIO& io = ImGui::GetIO();

	ImGui::SetNextWindowBgAlpha(config_.menu_alpha);
	if (ImGui::Begin("Statistics##overlay", &show_stats_window_, 
		ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoResize | 
		ImGuiWindowFlags_NoTitleBar)) {

		ImGui::Text("FPS: %.1f", io.Framerate);
		ImGui::Text("Frame Time: %.2f ms", 1000.0f / io.Framerate);
		ImGui::Text("Resolution: %dx%d", config_.window_width, config_.window_height);
		ImGui::Text("ASCII Grid: %dx%d", 
				   config_.get_ascii_width(), 
				   config_.get_ascii_height());

		ImGui::End();
	}
}

} // namespace gui
