#pragma once

#include <string>

namespace utils {

// Построить рамп символов, отсортированный по яркости
std::string build_char_ramp(const char* chars);

// Найти ближайший символ по яркости
char find_char_by_luminance(float luminance, const std::string& char_ramp);

}  // namespace utils
