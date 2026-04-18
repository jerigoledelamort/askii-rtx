#include "ascii_renderer.h"
#include <cmath>
#include <algorithm>

namespace gui {

AsciiRenderer::AsciiRenderer(int width, int height)
	: width_(width), height_(height) {
	rgb_buffer_.resize(width * height * 3, 0.5f);
	ascii_buffer_.resize((width / char_width_) * (height / char_height_), ' ');
	pixel_buffer_.resize(width * height, 0xFF000000);
}

AsciiRenderer::~AsciiRenderer() {
	cleanup();
}

bool AsciiRenderer::initialize() {
	// Инициализация буферов
	std::fill(rgb_buffer_.begin(), rgb_buffer_.end(), 0.5f);
	std::fill(ascii_buffer_.begin(), ascii_buffer_.end(), ' ');
	std::fill(pixel_buffer_.begin(), pixel_buffer_.end(), 0xFF000000);
	return true;
}

void AsciiRenderer::cleanup() {
	rgb_buffer_.clear();
	ascii_buffer_.clear();
	pixel_buffer_.clear();
}

void AsciiRenderer::clear() {
	std::fill(pixel_buffer_.begin(), pixel_buffer_.end(), 0xFF000000);
}

void AsciiRenderer::resize(int width, int height) {
	if (width <= 0 || height <= 0) return;

	width_ = width;
	height_ = height;

	rgb_buffer_.resize(width * height * 3, 0.5f);
	int ascii_w = width / char_width_;
	int ascii_h = height / char_height_;
	ascii_buffer_.resize(ascii_w * ascii_h, ' ');
	pixel_buffer_.resize(width * height, 0xFF000000);
}

void AsciiRenderer::render_scene(float time, const glm::vec3& camera_pos, const glm::vec3& camera_rot) {
	clear();
	update_rgb_buffer(time, camera_pos, camera_rot);
	rgb_to_ascii();
	ascii_to_pixels();
}

void AsciiRenderer::update_rgb_buffer(float time, const glm::vec3& camera_pos, const glm::vec3& camera_rot) {
	// Симуляция 3D сцены через градиент
	// На основе позиции камеры и времени

	for (int y = 0; y < height_; ++y) {
		for (int x = 0; x < width_; ++x) {
			int idx = (y * width_ + x) * 3;

			// Базовый градиент
			float fx = static_cast<float>(x) / width_;
			float fy = static_cast<float>(y) / height_;

			// Применяем волну на основе времени и позиции камеры
			float wave_x = std::sin(fx * 3.14159f * 4.0f + time * 0.5f + camera_pos.x);
			float wave_y = std::cos(fy * 3.14159f * 4.0f + time * 0.5f + camera_pos.z);
			float wave_t = std::sin(time * 0.3f) * 0.5f + 0.5f;

			// RGB каналы с анимацией
			rgb_buffer_[idx] = (0.5f + 0.5f * wave_x) * wave_t;           // R
			rgb_buffer_[idx + 1] = (0.5f + 0.5f * wave_y) * (1.0f - wave_t);  // G
			rgb_buffer_[idx + 2] = (fx + fy) * 0.5f + 0.25f;                  // B

			// Добавляем влияние позиции камеры
			float cam_dist = std::sqrt(camera_pos.x * camera_pos.x + camera_pos.z * camera_pos.z);
			rgb_buffer_[idx] *= (0.5f + 0.5f * std::sin(cam_dist + time));
		}
	}
}

void AsciiRenderer::rgb_to_ascii() {
	int ascii_w = get_ascii_width();
	int ascii_h = get_ascii_height();
	const int ramp_size = 10;  // " .:-=+*#%@"

	for (int y = 0; y < ascii_h; ++y) {
		for (int x = 0; x < ascii_w; ++x) {
			// Берём пиксель с шагом char_width/char_height
			int px = x * char_width_;
			int py = y * char_height_;

			// Вычисляем среднюю яркость в блоке
			float lum = 0.0f;
			int count = 0;

			for (int dy = 0; dy < char_height_ && (py + dy) < height_; ++dy) {
				for (int dx = 0; dx < char_width_ && (px + dx) < width_; ++dx) {
					int idx = ((py + dy) * width_ + (px + dx)) * 3;
					float r = rgb_buffer_[idx];
					float g = rgb_buffer_[idx + 1];
					float b = rgb_buffer_[idx + 2];

					lum += 0.299f * r + 0.587f * g + 0.114f * b;
					count++;
				}
			}

			if (count > 0) {
				lum /= count;
			}

			lum = std::max(0.0f, std::min(1.0f, lum));
			int char_idx = static_cast<int>(lum * (ramp_size - 1));
			ascii_buffer_[y * ascii_w + x] = char_ramp_[char_idx];
		}
	}
}

void AsciiRenderer::ascii_to_pixels() {
	int ascii_w = get_ascii_width();
	int ascii_h = get_ascii_height();

	for (int y = 0; y < ascii_h; ++y) {
		for (int x = 0; x < ascii_w; ++x) {
			char c = ascii_buffer_[y * ascii_w + x];

			// Рендеринг символа в блок пикселей
			for (int dy = 0; dy < char_height_ && (y * char_height_ + dy) < height_; ++dy) {
				for (int dx = 0; dx < char_width_ && (x * char_width_ + dx) < width_; ++dx) {
					int px = x * char_width_ + dx;
					int py = y * char_height_ + dy;
					int pidx = py * width_ + px;

					if (pidx < static_cast<int>(pixel_buffer_.size())) {
						// Базовый цвет - зелёный (классический ASCII арт)
						uint8_t brightness = static_cast<uint8_t>(c * 25);  // Яркость на основе символа
						pixel_buffer_[pidx] = 0xFF000000 | (brightness << 8);  // Green channel
					}
				}
			}
		}
	}
}

uint32_t AsciiRenderer::render_char(char c, int x, int y) {
	// Простой рендеринг символа как одного пикселя с разной яркостью
	uint8_t brightness = static_cast<uint8_t>((static_cast<int>(c) * 25) % 256);
	return 0xFF000000 | (brightness << 8);
}

void AsciiRenderer::get_framebuffer(std::vector<uint32_t>& out_pixels) const {
	out_pixels = pixel_buffer_;
}

} // namespace gui
