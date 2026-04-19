#ifndef ASCII_RENDERER_H
#define ASCII_RENDERER_H

#include <vector>
#include <cstdint>
#include <glm/glm.hpp>

class GpuRender;

namespace gui {

class AsciiRenderer {
public:
	AsciiRenderer(int width, int height);
	~AsciiRenderer();

	bool initialize();
	void cleanup();

	void clear();
	// Камера задаётся через set_camera() каждый кадр
	void render_scene(float time);
	void get_framebuffer(std::vector<uint32_t>& out_pixels) const;

	int get_width() const { return ascii_width_; }
	int get_height() const { return ascii_height_; }

	void set_resolution(int width, int height);
	void set_ascii_grid(int ascii_width, int ascii_height);
	void set_char_size(int w, int h);
	void set_camera(const glm::vec3& position, const glm::vec3& rotation_pitch_yaw_roll);

	void reset_accumulation_buffer();

	// Совместимость: только обновляет логическое разрешение полотна
	void resize(int width, int height);

private:
	int resolution_width_ = 1280;
	int resolution_height_ = 720;
	int ascii_width_ = 106;
	int ascii_height_ = 30;
	int char_width_ = 12;
	int char_height_ = 24;

	glm::vec3 camera_pos_{0.0f};
	glm::vec3 camera_rot_{0.0f};

	GpuRender* gpu_render_ = nullptr;

	std::vector<float> rgb_buffer_;
	std::vector<float> luminance_buffer_;
	std::vector<char> ascii_buffer_;
	std::vector<uint32_t> pixel_buffer_;

	const char* char_ramp_ = " .:-=+*#%@";

	void rebuild_gpu_if_needed();
	void update_rgb_buffer(float time);
	void rgb_to_ascii();
	void ascii_to_pixels();
	uint32_t render_char(char c, int x, int y);
};

} // namespace gui

#endif
