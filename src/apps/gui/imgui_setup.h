#pragma once

#include <cstdint>
#include "app_config.h"

namespace gui {

class ImGuiSetup {
public:
	static bool initialize(int width, int height);
	static void shutdown();
	static void new_frame();
	static void render();

	static void setup_style();
	static void setup_fonts();
};

class ImGuiMenu {
public:
	ImGuiMenu(AppConfig& config) : config_(config) {}

	void draw();

private:
	AppConfig& config_;

	// Состояние меню
	bool show_config_menu_ = true;
	bool show_stats_window_ = true;

	void draw_config_window();
	void draw_stats_window();
	void draw_main_menu_bar();
};

} // namespace gui
