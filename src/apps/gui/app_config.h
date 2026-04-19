#pragma once

#include <string>
#include <glm/glm.hpp>

namespace gui {

struct AppConfig {
	// Окно (клиентская область / swap chain)
	int window_width = 1280;
	int window_height = 720;

	// Логическое разрешение «полотна» для сетки ASCII (обычно = окно)
	int resolution_width = 1280;
	int resolution_height = 720;

	// Сетка символов: пересчёт из resolution / char (см. refresh_ascii_grid)
	int ascii_width = 106;
	int ascii_height = 30;

	bool fullscreen = false;
	bool vsync = true;

	// Размер «ячейки» в пикселях UI
	int char_width = 12;
	int char_height = 24;

	// Сцена
	int num_objects = 4;
	float animation_speed = 1.0f;

	// Камера
	glm::vec3 camera_pos = glm::vec3(0.0f, 1.5f, 4.0f);
	glm::vec3 camera_rot = glm::vec3(0.0f);
	float camera_speed = 0.1f;
	float camera_rotate_speed = 0.05f;
	bool auto_rotate = false;

	// Рендеринг
	bool show_stats = true;
	bool show_menu = true;
	float render_scale = 1.0f;

	// UI
	float menu_alpha = 0.9f;

	// Изменение разрешения / сетки / char — нужен rebuild + сброс accumulation + D3D texture
	bool config_dirty = false;

	// Сброс камеры из UI (обрабатывается в main::update)
	bool camera_reset_requested = false;

	void refresh_ascii_grid();
	void sync_resolution_with_window();

	bool load_from_file(const std::string& filename);
	bool save_to_file(const std::string& filename) const;

	int get_ascii_width() const { return ascii_width; }
	int get_ascii_height() const { return ascii_height; }
};

} // namespace gui
