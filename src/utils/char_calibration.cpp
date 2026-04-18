#include "char_calibration.h"
#include <algorithm>
#include <vector>
#include <cmath>

namespace utils {

std::string build_char_ramp(const char* chars) {
	// В этом движке мы используем преопределённую рамп
	// Полная реализация требовала бы рендеринга каждого символа в буфер
	// Для простоты мы используем эмпирический порядок символов по яркости

	std::string ramp(chars);
	// Символы уже отсортированы от темных к светлым: " .,:-~=+*#%@"
	return ramp;
}

char find_char_by_luminance(float luminance, const std::string& char_ramp) {
	// Зажимаем люминанс в [0, 1]
	luminance = std::max(0.0f, std::min(1.0f, luminance));

	// Преобразуем люминанс в индекс символа
	int index = static_cast<int>(luminance * (char_ramp.length() - 1));
	index = std::max(0, std::min(static_cast<int>(char_ramp.length() - 1), index));

	return char_ramp[index];
}

}  // namespace utils
