#ifndef ASCII_RENDERER_H
#define ASCII_RENDERER_H

#include <vector>
#include <cstdint>
#include <glm/glm.hpp>

namespace gui {

class AsciiRenderer {
public:
	AsciiRenderer(int width, int height);
	~AsciiRenderer();

	// Инициализация
	bool initialize();
	void cleanup();

	// Рендеринг
	void clear();
	void render_scene(float time, const glm::vec3& camera_pos, const glm::vec3& camera_rot);
	void get_framebuffer(std::vector<uint32_t>& out_pixels) const;

	// Параметры
	int get_width() const { return width_; }
	int get_height() const { return height_; }
	void resize(int width, int height);

	// ASCII параметры
	void set_char_size(int w, int h) { char_width_ = w; char_height_ = h; }
	int get_ascii_width() const { return width_ / char_width_; }
	int get_ascii_height() const { return height_ / char_height_; }

private:
	int width_;
	int height_;
	int char_width_ = 12;
	int char_height_ = 24;

	// RGB буфер
	std::vector<float> rgb_buffer_;

	// ASCII буфер
	std::vector<char> ascii_buffer_;

	// Пиксельный буфер для визуализации
	std::vector<uint32_t> pixel_buffer_;

	// ASCII палитра
	const char* char_ramp_ = " .:-=+*#%@";

	// Приватные методы
	void update_rgb_buffer(float time, const glm::vec3& camera_pos, const glm::vec3& camera_rot);
	void rgb_to_ascii();
	void ascii_to_pixels();
	uint32_t render_char(char c, int x, int y);
};

} // namespace gui

#endif // ASCII_RENDERER_H
