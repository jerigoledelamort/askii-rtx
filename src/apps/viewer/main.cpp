#include <iostream>
#include <cstring>
#include <cmath>
#include <chrono>

#include "engine/core.h"
#include "config/default.h"
#include "utils/char_calibration.h"
#include "apps/viewer/ui.h"

// Simple framebuffer for ASCII rendering
struct ASCIIFramebuffer {
	char* data;
	int width, height;

	ASCIIFramebuffer(int w, int h) : width(w), height(h) {
		data = new char[w * h + 1];
		memset(data, ' ', w * h);
		data[w * h] = '\0';
	}

	~ASCIIFramebuffer() {
		delete[] data;
	}

	void set_char(int x, int y, char c) {
		if (x >= 0 && x < width && y >= 0 && y < height) {
			data[y * width + x] = c;
		}
	}

	void clear() {
		memset(data, ' ', width * height);
	}

	void print() {
		for (int y = 0; y < height; ++y) {
			for (int x = 0; x < width; ++x) {
				std::cout << data[y * width + x];
			}
			std::cout << "\n";
		}
	}
};

// Convert RGB luminance to ASCII
void rgb_to_ascii(
	const float* rgb_buffer,
	int width, int height,
	ASCIIFramebuffer& ascii_fb,
	const std::string& char_ramp
) {
	ascii_fb.clear();

	// Downsampling factor - render at lower resolution to fit terminal
	int char_width = 80;   // Characters in horizontal
	int char_height = 24;  // Characters in vertical

	float x_step = (float)width / (float)char_width;
	float y_step = (float)height / (float)char_height;

	for (int cy = 0; cy < char_height; ++cy) {
		for (int cx = 0; cx < char_width; ++cx) {
			int px = (int)(cx * x_step);
			int py = (int)(cy * y_step);

			if (px >= width) px = width - 1;
			if (py >= height) py = height - 1;

			int pixel_idx = (py * width + px) * 3;
			float r = rgb_buffer[pixel_idx + 0];
			float g = rgb_buffer[pixel_idx + 1];
			float b = rgb_buffer[pixel_idx + 2];

			float lum = 0.299f * r + 0.587f * g + 0.114f * b;
			char ch = utils::find_char_by_luminance(lum, char_ramp);

			ascii_fb.set_char(cx, cy, ch);
		}
	}
}

int main() {
	std::cout << "=== ASCII RTX v1 - Ray Tracing Engine ===" << std::endl;
	std::cout << "Initializing..." << std::endl;

	// Initialize configuration
	config::init_default_config();
	materials::init_materials();

	// Get terminal size
	int window_width = 1280;
	int window_height = 720;

	std::cout << "Creating engine (" << window_width << "x" << window_height << ")..." << std::endl;

	Engine engine(window_width, window_height);
	engine.initialize();

	// Create ASCII framebuffer
	ASCIIFramebuffer ascii_fb(80, 24);
	std::string char_ramp = utils::build_char_ramp(config::g_config.render.chars);

	// UI
	UI ui(window_width, window_height);

	std::cout << "Starting render loop..." << std::endl;
	std::cout << "Press Ctrl+C to exit" << std::endl;
	std::cout << std::endl;

	// Render loop
	auto last_time = std::chrono::high_resolution_clock::now();
	int frame_count = 0;
	float total_time = 0.0f;

	for (int frame = 0; frame < 500; ++frame) {  // Render 500 frames
		auto current_time = std::chrono::high_resolution_clock::now();
		auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
			current_time - last_time
		);
		float delta_time = duration.count() / 1000.0f;
		last_time = current_time;

		// Update
		engine.update(delta_time);

		// Render
		engine.render();

		// Get GPU buffers
		float* rgb_buffer = engine.get_render()->get_rgb_buffer();

		// Copy to host if needed (in real implementation)
		// For now, just print frame info

		total_time += delta_time;
		frame_count++;

		if (frame % 30 == 0) {
			std::cout << "\rFrame: " << frame << " | FPS: " << (frame_count / total_time);
			std::cout.flush();
		}
	}

	std::cout << "\n\nRender complete!" << std::endl;
	std::cout << "Total frames: " << frame_count << std::endl;
	std::cout << "Total time: " << total_time << " seconds" << std::endl;
	std::cout << "Average FPS: " << (frame_count / total_time) << std::endl;

	return 0;
}
