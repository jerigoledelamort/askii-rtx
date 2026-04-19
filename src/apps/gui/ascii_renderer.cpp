#include "ascii_renderer.h"
#include "../../config/default.h"
#include "../../engine/materials.h"
#include "../../engine/render.h"
#include <cmath>
#include <algorithm>
#include <cstring>

namespace gui {

AsciiRenderer::AsciiRenderer(int width, int height)
	: resolution_width_(std::max(1, width)),
	  resolution_height_(std::max(1, height)) {
	char_width_ = std::max(1, char_width_);
	char_height_ = std::max(1, char_height_);
	ascii_width_ = std::max(1, resolution_width_ / char_width_);
	ascii_height_ = std::max(1, resolution_height_ / char_height_);
}

AsciiRenderer::~AsciiRenderer() {
	cleanup();
}

bool AsciiRenderer::initialize() {
	config::init_default_config();
	materials::init_materials();
	rebuild_gpu_if_needed();
	if (!gpu_render_) {
		return false;
	}
	std::fill(rgb_buffer_.begin(), rgb_buffer_.end(), 0.5f);
	std::fill(luminance_buffer_.begin(), luminance_buffer_.end(), 0.5f);
	std::fill(ascii_buffer_.begin(), ascii_buffer_.end(), ' ');
	std::fill(pixel_buffer_.begin(), pixel_buffer_.end(), 0xFF000000);
	return true;
}

void AsciiRenderer::cleanup() {
	if (gpu_render_) {
		delete gpu_render_;
		gpu_render_ = nullptr;
	}
	rgb_buffer_.clear();
	luminance_buffer_.clear();
	ascii_buffer_.clear();
	pixel_buffer_.clear();
}

void AsciiRenderer::clear() {
	std::fill(pixel_buffer_.begin(), pixel_buffer_.end(), 0xFF000000);
}

void AsciiRenderer::set_resolution(int width, int height) {
	resolution_width_ = std::max(1, width);
	resolution_height_ = std::max(1, height);
}

void AsciiRenderer::set_ascii_grid(int ascii_width, int ascii_height) {
	ascii_width_ = std::max(1, ascii_width);
	ascii_height_ = std::max(1, ascii_height);
	rebuild_gpu_if_needed();
}

void AsciiRenderer::set_char_size(int w, int h) {
	if (w <= 0 || h <= 0) {
		return;
	}
	char_width_ = w;
	char_height_ = h;
}

void AsciiRenderer::set_camera(const glm::vec3& position, const glm::vec3& rotation) {
	camera_pos_ = position;
	camera_rot_ = rotation;
}

void AsciiRenderer::reset_accumulation_buffer() {
	if (gpu_render_) {
		gpu_render_->reset_accumulation_buffer();
	}
}

void AsciiRenderer::resize(int width, int height) {
	set_resolution(width, height);
}

void AsciiRenderer::rebuild_gpu_if_needed() {
	if (gpu_render_ &&
		gpu_render_->get_width() == ascii_width_ &&
		gpu_render_->get_height() == ascii_height_) {
		return;
	}

	if (gpu_render_) {
		delete gpu_render_;
		gpu_render_ = nullptr;
	}

	gpu_render_ = new GpuRender(ascii_width_, ascii_height_);
	gpu_render_->initialize();

	rgb_buffer_.resize(static_cast<size_t>(ascii_width_) * static_cast<size_t>(ascii_height_) * 3, 0.0f);
	luminance_buffer_.resize(static_cast<size_t>(ascii_width_) * static_cast<size_t>(ascii_height_), 0.0f);
	ascii_buffer_.resize(static_cast<size_t>(ascii_width_) * static_cast<size_t>(ascii_height_), ' ');
	pixel_buffer_.resize(static_cast<size_t>(ascii_width_) * static_cast<size_t>(ascii_height_), 0xFF000000);
}

void AsciiRenderer::render_scene(float time) {
	clear();
	update_rgb_buffer(time);
	rgb_to_ascii();
	ascii_to_pixels();
}

void AsciiRenderer::update_rgb_buffer(float time) {
	if (!gpu_render_) {
		return;
	}

	float pitch = camera_rot_.x;
	float yaw = camera_rot_.y;
	glm::vec3 forward(
		std::sin(yaw) * std::cos(pitch),
		std::sin(pitch),
		-std::cos(yaw) * std::cos(pitch)
	);
	forward = glm::normalize(forward);

	glm::vec3 world_up(0.0f, 1.0f, 0.0f);
	glm::vec3 right = glm::normalize(glm::cross(forward, world_up));
	if (glm::dot(right, right) < 0.000001f) {
		right = glm::vec3(1.0f, 0.0f, 0.0f);
	}
	glm::vec3 up = glm::normalize(glm::cross(right, forward));

	gpu_render_->render_frame(
		camera_pos_,
		forward,
		right,
		up,
		config::g_config.camera.fov,
		1,
		time
	);

	float* rgb = gpu_render_->get_rgb_buffer();
	float* luminance = gpu_render_->get_luminance_buffer();

	for (int i = 0; i < ascii_width_ * ascii_height_ * 3; ++i) {
		rgb_buffer_[i] = rgb[i];
	}

	for (int i = 0; i < ascii_width_ * ascii_height_; ++i) {
		luminance_buffer_[i] = luminance[i];
	}
}

void AsciiRenderer::rgb_to_ascii() {
	const int ramp_size = static_cast<int>(std::strlen(char_ramp_));

	for (int i = 0; i < ascii_width_ * ascii_height_; ++i) {
		int rgb_idx = i * 3;
		glm::vec3 color(
			rgb_buffer_[rgb_idx],
			rgb_buffer_[rgb_idx + 1],
			rgb_buffer_[rgb_idx + 2]
		);
		float luminance = glm::dot(color, glm::vec3(0.2126f, 0.7152f, 0.0722f));
		luminance = std::max(0.0f, std::min(1.0f, luminance));
		luminance_buffer_[i] = luminance;
		int char_idx = static_cast<int>(luminance * static_cast<float>(ramp_size - 1));
		char_idx = std::clamp(char_idx, 0, ramp_size - 1);
		ascii_buffer_[i] = char_ramp_[char_idx];
	}
}

void AsciiRenderer::ascii_to_pixels() {
	for (int i = 0; i < ascii_width_ * ascii_height_; ++i) {
		uint8_t gray = static_cast<uint8_t>(
			std::max(0.0f, std::min(255.0f, luminance_buffer_[i] * 255.0f))
		);
		pixel_buffer_[i] = 0xFF000000u |
			(static_cast<uint32_t>(gray) << 16) |
			(static_cast<uint32_t>(gray) << 8) |
			static_cast<uint32_t>(gray);
	}
}

uint32_t AsciiRenderer::render_char(char c, int x, int y) {
	(void)c;
	(void)x;
	(void)y;
	return 0xFF000000u;
}

void AsciiRenderer::get_framebuffer(std::vector<uint32_t>& out_pixels) const {
	out_pixels = pixel_buffer_;
}

} // namespace gui
