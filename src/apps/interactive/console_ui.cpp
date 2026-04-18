#include "console_ui.h"

#ifdef _WIN32
#include <windows.h>
#include <iostream>
#endif

namespace console {

ConsoleUI::ConsoleUI(int width, int height)
	: width_(width), height_(height), console_handle_(nullptr) {
}

ConsoleUI::~ConsoleUI() {
	cleanup();
}

bool ConsoleUI::initialize() {
#ifdef _WIN32
	console_handle_ = GetStdHandle(STD_OUTPUT_HANDLE);
	if (console_handle_ == INVALID_HANDLE_VALUE) {
		return false;
	}

	// Пытаемся установить размер буфера (может не сработать)
	COORD buffer_size = {static_cast<SHORT>(width_), static_cast<SHORT>(height_)};
	SetConsoleScreenBufferSize((HANDLE)console_handle_, buffer_size);

	// Пытаемся установить размер окна (может не сработать)
	SMALL_RECT window_rect = {0, 0, static_cast<SHORT>(width_ - 1), static_cast<SHORT>(height_ - 1)};
	SetConsoleWindowInfo((HANDLE)console_handle_, TRUE, &window_rect);

	// Включение ANSI режима (если поддерживается)
	DWORD mode = 0;
	if (GetConsoleMode((HANDLE)console_handle_, &mode)) {
		mode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
		SetConsoleMode((HANDLE)console_handle_, mode);
	}

	hide_cursor();
	return true;  // Успех даже если некоторые операции не сработали
#else
	return false;
#endif
}

void ConsoleUI::cleanup() {
	if (console_handle_) {
		show_cursor();
		console_handle_ = nullptr;
	}
}

void ConsoleUI::clear() {
#ifdef _WIN32
	if (!console_handle_) return;

	COORD top_left = {0, 0};
	DWORD written = 0;
	DWORD size = width_ * height_;

	FillConsoleOutputCharacter((HANDLE)console_handle_, ' ', size, top_left, &written);
	FillConsoleOutputAttribute((HANDLE)console_handle_, FOREGROUND_GREEN | FOREGROUND_INTENSITY,
							   size, top_left, &written);
	SetConsoleCursorPosition((HANDLE)console_handle_, top_left);
#endif
}

void ConsoleUI::set_cursor_position(int x, int y) {
#ifdef _WIN32
	if (!console_handle_) return;
	COORD position = {static_cast<SHORT>(x), static_cast<SHORT>(y)};
	SetConsoleCursorPosition((HANDLE)console_handle_, position);
#endif
}

void ConsoleUI::write_at(int x, int y, const std::string& text) {
	set_cursor_position(x, y);
	std::cout << text;
	std::cout.flush();
}

void ConsoleUI::write_line(const std::string& text) {
	std::cout << text << "\n";
	std::cout.flush();
}

void ConsoleUI::hide_cursor() {
#ifdef _WIN32
	if (!console_handle_) return;

	CONSOLE_CURSOR_INFO cursor_info;
	GetConsoleCursorInfo((HANDLE)console_handle_, &cursor_info);
	cursor_info.bVisible = FALSE;
	SetConsoleCursorInfo((HANDLE)console_handle_, &cursor_info);
#endif
}

void ConsoleUI::show_cursor() {
#ifdef _WIN32
	if (!console_handle_) return;

	CONSOLE_CURSOR_INFO cursor_info;
	GetConsoleCursorInfo((HANDLE)console_handle_, &cursor_info);
	cursor_info.bVisible = TRUE;
	SetConsoleCursorInfo((HANDLE)console_handle_, &cursor_info);
#endif
}

void ConsoleUI::render_buffer(const std::vector<char>& buffer, int width, int height) {
	if (buffer.empty()) return;

#ifdef _WIN32
	set_cursor_position(0, 0);

	for (int y = 0; y < height && y < height_; ++y) {
		for (int x = 0; x < width && x < width_; ++x) {
			int idx = y * width + x;
			if (idx < static_cast<int>(buffer.size())) {
				std::cout << buffer[idx];
			}
		}
		std::cout << "\n";
	}
	std::cout.flush();
#endif
}

void ConsoleUI::render_frame(const std::vector<char>& ascii_frame, int width, int height,
							float fps, const std::string& info) {
	clear();

	// Верхняя информационная строка
	set_cursor_position(0, 0);
	char fps_str[64];
	sprintf_s(fps_str, 64, "FPS: %.1f", fps);
	std::cout << fps_str << "  " << info;
	std::cout.flush();

	// ASCII контент
	if (!ascii_frame.empty()) {
		set_cursor_position(0, 2);

		for (int y = 0; y < height && (y + 2) < height_; ++y) {
			for (int x = 0; x < width && x < width_; ++x) {
				int idx = y * width + x;
				if (idx < static_cast<int>(ascii_frame.size())) {
					char c = ascii_frame[idx];
					// Избегаем управляющих символов
					if (c >= 32 && c < 127) {
						std::cout << c;
					} else {
						std::cout << ' ';
					}
				}
			}
			std::cout << "\n";
		}
		std::cout.flush();
	}
}

} // namespace console
