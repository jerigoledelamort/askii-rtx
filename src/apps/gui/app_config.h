#pragma once

#include <string>
#include <glm/glm.hpp>

namespace gui {

struct AppConfig {
	// Видео параметры
	int window_width = 1280;
	int window_height = 720;
	bool fullscreen = false;
	bool vsync = true;

	// ASCII параметры
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
	bool auto_rotate = true;

	// Рендеринг
	bool show_stats = true;
	bool show_menu = true;
	float render_scale = 1.0f;

	// UI
	float menu_alpha = 0.9f;

	// Методы сохранения/загрузки
	bool load_from_file(const std::string& filename);
	bool save_to_file(const std::string& filename) const;

	// Вычисленные параметры
	int get_ascii_width() const { return window_width / char_width; }
	int get_ascii_height() const { return window_height / char_height; }
};

} // namespace gui
