#include "input_handler.h"

#ifdef _WIN32
#include <windows.h>
#include <cmath>
#endif

namespace input {

InputHandler::InputHandler() : enabled_(true) {
}

InputHandler::~InputHandler() {
}

bool InputHandler::is_key_pressed(int key) {
#ifdef _WIN32
	return (GetAsyncKeyState(key) & 0x8000) != 0;
#else
	return false;
#endif
}

CameraInput InputHandler::process_input() {
	CameraInput input = {};
	input.position_delta = glm::vec3(0.0f);
	input.rotation_delta = glm::vec3(0.0f);
	input.should_exit = false;
	input.should_reset = false;

	if (!enabled_) {
		return input;
	}

	const float move_speed = 0.1f;      // Скорость движения
	const float rotate_speed = 0.05f;   // Скорость вращения

	// Проверка управления движением (WASD)
	if (is_key_pressed('W')) {
		input.position_delta.z += move_speed;  // Вперёд
	}
	if (is_key_pressed('S')) {
		input.position_delta.z -= move_speed;  // Назад
	}
	if (is_key_pressed('A')) {
		input.position_delta.x -= move_speed;  // Влево
	}
	if (is_key_pressed('D')) {
		input.position_delta.x += move_speed;  // Вправо
	}

	// Вертикальное движение (Q/E)
	if (is_key_pressed('Q')) {
		input.position_delta.y -= move_speed;  // Вниз
	}
	if (is_key_pressed('E')) {
		input.position_delta.y += move_speed;  // Вверх
	}

	// Управление камерой (Стрелки)
	if (is_key_pressed(VK_UP)) {
		input.rotation_delta.x -= rotate_speed;  // Поворот вверх (pitch)
	}
	if (is_key_pressed(VK_DOWN)) {
		input.rotation_delta.x += rotate_speed;  // Поворот вниз (pitch)
	}
	if (is_key_pressed(VK_LEFT)) {
		input.rotation_delta.y -= rotate_speed;  // Поворот влево (yaw)
	}
	if (is_key_pressed(VK_RIGHT)) {
		input.rotation_delta.y += rotate_speed;  // Поворот вправо (yaw)
	}

	// Горячие клавиши
	if (is_key_pressed(VK_ESCAPE)) {
		input.should_exit = true;
	}
	if (is_key_pressed('R')) {
		input.should_reset = true;
	}

	return input;
}

void InputHandler::enable() {
	enabled_ = true;
}

void InputHandler::disable() {
	enabled_ = false;
}

} // namespace input
