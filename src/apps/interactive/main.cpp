#include <iostream>
#include <chrono>
#include <thread>
#include <vector>
#include <sstream>
#include <iomanip>

#include "engine/core.h"
#include "config/default.h"
#include "utils/char_calibration.h"
#include "console_ui.h"
#include "input_handler.h"

class InteractiveViewer {
private:
	Engine engine_;
	console::ConsoleUI console_ui_;
	input::InputHandler input_handler_;

	int frame_count_;
	std::chrono::high_resolution_clock::time_point last_fps_time_;
	float current_fps_;

	// ASCII параметры
	int ascii_width_;
	int ascii_height_;
	std::vector<char> ascii_buffer_;
	std::vector<float> rgb_buffer_;

	// Камера управление
	glm::vec3 camera_pos_;
	glm::vec3 camera_rot_;
	glm::vec3 camera_initial_pos_;

	const char* char_ramp_ = " .:-=+*#%@";

public:
	InteractiveViewer() 
		: engine_(100, 28),
		  console_ui_(120, 40), 
		  frame_count_(0), 
		  current_fps_(0.0f),
		  ascii_width_(100),
		  ascii_height_(28),
		  camera_pos_(0.0f, 1.0f, 3.0f),
		  camera_rot_(0.0f),
		  camera_initial_pos_(camera_pos_) {
		ascii_buffer_.resize(ascii_width_ * ascii_height_, ' ');
		rgb_buffer_.resize(ascii_width_ * ascii_height_ * 3, 0.5f);
	}

	bool initialize() {
		// Инициализация конфига
		config::init_default_config();

		// Инициализация движка
		try {
			engine_.initialize();
		}
		catch (const std::exception& e) {
			std::cerr << "[ERROR] Failed to initialize engine: " << e.what() << "\n";
			return false;
		}

		// Инициализация консоли
		if (!console_ui_.initialize()) {
			std::cerr << "[ERROR] Failed to initialize console UI\n";
			return false;
		}

		console_ui_.hide_cursor();
		last_fps_time_ = std::chrono::high_resolution_clock::now();

		return true;
	}

	void cleanup() {
		console_ui_.cleanup();
		console_ui_.show_cursor();
	}

	void run() {
		std::cout << "\n";
		std::cout << "╔════════════════════════════════════════════════════════════════╗\n";
		std::cout << "║                                                                ║\n";
		std::cout << "║         ASCII RTX v1 - Interactive Ray Tracing Engine          ║\n";
		std::cout << "║                                                                ║\n";
		std::cout << "║  Controls:                                                     ║\n";
		std::cout << "║    WASD  - Move camera (forward/back, left/right)            ║\n";
		std::cout << "║    Q/E   - Move camera (down/up)                             ║\n";
		std::cout << "║    ↑↓←→  - Rotate camera (pitch/yaw)                         ║\n";
		std::cout << "║    R     - Reset camera position                             ║\n";
		std::cout << "║    ESC   - Exit                                              ║\n";
		std::cout << "║                                                                ║\n";
		std::cout << "╚════════════════════════════════════════════════════════════════╝\n";

		std::this_thread::sleep_for(std::chrono::seconds(2));

		bool running = true;
		while (running) {
			auto frame_start = std::chrono::high_resolution_clock::now();

			// Обработка ввода
			input::CameraInput input = input_handler_.process_input();

			if (input.should_exit) {
				running = false;
				break;
			}

			if (input.should_reset) {
				camera_pos_ = camera_initial_pos_;
				camera_rot_ = glm::vec3(0.0f);
			}

			// Применение движения камеры
			camera_pos_ += input.position_delta;
			camera_rot_ += input.rotation_delta;

			// Ограничение pitch угла
			camera_rot_.x = glm::clamp(camera_rot_.x, -1.57f, 1.57f);

			// Обновление позиции камеры в движке
			engine_.get_camera().set_position(camera_pos_);

			// Обновление сцены
			engine_.update(0.016f);  // ~60 FPS target

			// Рендеринг
			engine_.render();

			// Получение RGB буфера из движка (симуляция)
			update_rgb_buffer();

			// Конвертация в ASCII
			rgb_to_ascii();

			// Обновление FPS
			update_fps();

			// Построение информационной строки
			std::ostringstream info;
			info << "Cam: [" << std::fixed << std::setprecision(1)
				 << camera_pos_.x << ", " << camera_pos_.y << ", " 
				 << camera_pos_.z << "]";

			// Рендеринг на консоль
			console_ui_.render_frame(ascii_buffer_, ascii_width_, ascii_height_, 
									 current_fps_, info.str());

			// Ограничение FPS (~60 FPS)
			auto frame_end = std::chrono::high_resolution_clock::now();
			auto frame_duration = std::chrono::duration_cast<std::chrono::milliseconds>(
				frame_end - frame_start);

			const int target_ms = 16;  // ~60 FPS
			if (frame_duration.count() < target_ms) {
				std::this_thread::sleep_for(
					std::chrono::milliseconds(target_ms - frame_duration.count()));
			}
		}
	}

private:
	void update_rgb_buffer() {
		// Симуляция получения RGB буфера из движка
		for (int i = 0; i < static_cast<int>(rgb_buffer_.size()); i += 3) {
			float t = static_cast<float>(frame_count_) * 0.01f;
			rgb_buffer_[i] = 0.5f + 0.5f * std::sin(t + i * 0.01f);      // R
			rgb_buffer_[i + 1] = 0.5f + 0.5f * std::sin(t + i * 0.02f);  // G
			rgb_buffer_[i + 2] = 0.5f + 0.5f * std::sin(t + i * 0.03f);  // B
		}
	}

	void rgb_to_ascii() {
		const int ramp_size = 10;  // " .:-=+*#%@"

		for (int y = 0; y < ascii_height_; ++y) {
			for (int x = 0; x < ascii_width_; ++x) {
				int idx = y * ascii_width_ + x;
				int rgb_idx = idx * 3;

				// Вычисление яркости (luminance)
				float r = rgb_buffer_[rgb_idx];
				float g = rgb_buffer_[rgb_idx + 1];
				float b = rgb_buffer_[rgb_idx + 2];

				float luminance = 0.299f * r + 0.587f * g + 0.114f * b;
				luminance = std::max(0.0f, std::min(1.0f, luminance));

				// Маппинг на символ
				int char_idx = static_cast<int>(luminance * (ramp_size - 1));
				ascii_buffer_[idx] = char_ramp_[char_idx];
			}
		}
	}

	void update_fps() {
		frame_count_++;
		auto now = std::chrono::high_resolution_clock::now();
		auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
			now - last_fps_time_).count();

		if (elapsed >= 1000) {  // Обновление каждую секунду
			current_fps_ = frame_count_ * 1000.0f / elapsed;
			frame_count_ = 0;
			last_fps_time_ = now;
		}
	}
};

int main() {
	try {
		InteractiveViewer viewer;

		if (!viewer.initialize()) {
			std::cerr << "[ERROR] Failed to initialize viewer\n";
			return 1;
		}

		viewer.run();
		viewer.cleanup();

		std::cout << "\n[INFO] Application closed successfully\n";
		return 0;
	}
	catch (const std::exception& e) {
		std::cerr << "[EXCEPTION] " << e.what() << "\n";
		return 1;
	}
}
