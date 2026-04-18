#ifndef CONSOLE_UI_H
#define CONSOLE_UI_H

#include <string>
#include <vector>
#include <cstdint>

namespace console {

class ConsoleUI {
public:
	ConsoleUI(int width = 100, int height = 30);
	~ConsoleUI();

	// Инициализация консоли
	bool initialize();
	void cleanup();

	// Вывод текста
	void clear();
	void set_cursor_position(int x, int y);
	void write_at(int x, int y, const std::string& text);
	void write_line(const std::string& text);

	// Рендеринг буфера
	void render_buffer(const std::vector<char>& buffer, int width, int height);
	void render_frame(const std::vector<char>& ascii_frame, int width, int height,
					 float fps, const std::string& info);

	// Получение размеров
	int get_width() const { return width_; }
	int get_height() const { return height_; }

	// Скрытие курсора
	void hide_cursor();
	void show_cursor();

private:
	int width_;
	int height_;
	void* console_handle_;
};

} // namespace console

#endif // CONSOLE_UI_H
