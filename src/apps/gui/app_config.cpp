#include "app_config.h"
#include <algorithm>
#include <fstream>
#include <sstream>

namespace gui {

void AppConfig::refresh_ascii_grid() {
	const int cw = std::max(1, char_width);
	const int ch = std::max(1, char_height);
	const int rw = std::max(1, resolution_width);
	const int rh = std::max(1, resolution_height);
	ascii_width = std::max(1, rw / cw);
	ascii_height = std::max(1, rh / ch);
}

void AppConfig::sync_resolution_with_window() {
	resolution_width = std::max(1, window_width);
	resolution_height = std::max(1, window_height);
	refresh_ascii_grid();
}

bool AppConfig::load_from_file(const std::string& filename) {
	std::ifstream file(filename);
	if (!file.is_open()) {
		sync_resolution_with_window();
		return false;
	}

	bool have_resolution_keys = false;
	std::string line;
	while (std::getline(file, line)) {
		if (line.empty() || line[0] == ';') continue;

		std::istringstream iss(line);
		std::string key, value;

		if (!std::getline(iss, key, '=')) continue;
		if (!std::getline(iss, value)) continue;

		key.erase(0, key.find_first_not_of(" \t"));
		key.erase(key.find_last_not_of(" \t") + 1);
		value.erase(0, value.find_first_not_of(" \t"));
		value.erase(value.find_last_not_of(" \t") + 1);

		if (key == "window_width") window_width = std::stoi(value);
		else if (key == "window_height") window_height = std::stoi(value);
		else if (key == "resolution_width") {
			resolution_width = std::stoi(value);
			have_resolution_keys = true;
		} else if (key == "resolution_height") {
			resolution_height = std::stoi(value);
			have_resolution_keys = true;
		}
		else if (key == "fullscreen") fullscreen = (value == "true" || value == "1");
		else if (key == "vsync") vsync = (value == "true" || value == "1");
		else if (key == "char_width") char_width = std::stoi(value);
		else if (key == "char_height") char_height = std::stoi(value);
		else if (key == "animation_speed") animation_speed = std::stof(value);
		else if (key == "auto_rotate") auto_rotate = (value == "true" || value == "1");
		else if (key == "camera_speed") camera_speed = std::stof(value);
		else if (key == "camera_rotate_speed") camera_rotate_speed = std::stof(value);
		else if (key == "num_objects") num_objects = std::stoi(value);
		else if (key == "show_stats") show_stats = (value == "true" || value == "1");
	}

	file.close();

	if (!have_resolution_keys) {
		resolution_width = std::max(1, window_width);
		resolution_height = std::max(1, window_height);
	}
	resolution_width = std::max(1, resolution_width);
	resolution_height = std::max(1, resolution_height);
	window_width = std::max(1, window_width);
	window_height = std::max(1, window_height);
	refresh_ascii_grid();
	return true;
}

bool AppConfig::save_to_file(const std::string& filename) const {
	std::ofstream file(filename);
	if (!file.is_open()) {
		return false;
	}

	file << "; ASCII RTX v1 - GUI Application Configuration\n\n";

	file << "[VIDEO]\n";
	file << "window_width=" << window_width << "\n";
	file << "window_height=" << window_height << "\n";
	file << "resolution_width=" << resolution_width << "\n";
	file << "resolution_height=" << resolution_height << "\n";
	file << "fullscreen=" << (fullscreen ? "true" : "false") << "\n";
	file << "vsync=" << (vsync ? "true" : "false") << "\n";

	file << "\n[ASCII]\n";
	file << "char_width=" << char_width << "\n";
	file << "char_height=" << char_height << "\n";

	file << "\n[CAMERA]\n";
	file << "camera_speed=" << camera_speed << "\n";
	file << "camera_rotate_speed=" << camera_rotate_speed << "\n";
	file << "auto_rotate=" << (auto_rotate ? "true" : "false") << "\n";

	file << "\n[SCENE]\n";
	file << "animation_speed=" << animation_speed << "\n";
	file << "num_objects=" << num_objects << "\n";

	file << "\n[UI]\n";
	file << "show_stats=" << (show_stats ? "true" : "false") << "\n";

	file.close();
	return true;
}

} // namespace gui
