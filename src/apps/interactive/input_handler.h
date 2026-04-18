#ifndef INPUT_HANDLER_H
#define INPUT_HANDLER_H

#include <glm/glm.hpp>

namespace input {

struct CameraInput {
	glm::vec3 position_delta;  // Движение вперёд/назад/влево/вправо
	glm::vec3 rotation_delta;  // Вращение (pitch, yaw, roll)
	bool should_exit;
	bool should_reset;
};

class InputHandler {
public:
	InputHandler();
	~InputHandler();

	// Обработка ввода (неблокирующая)
	CameraInput process_input();

	// Включение/отключение обработки
	void enable();
	void disable();

private:
	bool enabled_;

	// Windows API специфичные методы
	bool is_key_pressed(int key);
};

} // namespace input

#endif // INPUT_HANDLER_H
