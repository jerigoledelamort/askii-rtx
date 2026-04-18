#include "ui.h"
#include <cmath>
#include <algorithm>

// ============ SLIDER ============

Slider::Slider(int x, int y, int width, int height, float min_val, float max_val, float initial)
	: x(x), y(y), width(width), height(height), min_value(min_val), max_value(max_val),
	  value(initial), dragging(false) {
}

void Slider::render() {
	// Placeholder: in real implementation would use SDL2 or similar
}

void Slider::handle_mouse(int mx, int my, bool clicked) {
	if (is_hovered(mx, my)) {
		if (clicked) {
			dragging = true;
		}
	}

	if (!clicked) {
		dragging = false;
	}

	if (dragging) {
		float t = (float)(mx - x) / (float)width;
		t = std::max(0.0f, std::min(1.0f, t));
		value = min_value + t * (max_value - min_value);
	}
}

bool Slider::is_hovered(int mx, int my) const {
	return mx >= x && mx <= x + width && my >= y && my <= y + height;
}

// ============ BUTTON ============

Button::Button(int x, int y, int width, int height, const std::string& label)
	: x(x), y(y), width(width), height(height), label(label), pressed(false), hovered(false) {
}

void Button::render() {
	// Placeholder
}

void Button::handle_mouse(int mx, int my, bool clicked) {
	hovered = is_hovered(mx, my);
	if (hovered && clicked) {
		pressed = true;
	}
}

bool Button::is_hovered(int mx, int my) const {
	return mx >= x && mx <= x + width && my >= y && my <= y + height;
}

// ============ CHECKBOX ============

Checkbox::Checkbox(int x, int y, const std::string& label, bool initial)
	: x(x), y(y), size(20), label(label), checked(initial) {
}

void Checkbox::render() {
	// Placeholder
}

void Checkbox::handle_mouse(int mx, int my, bool clicked) {
	if (is_hovered(mx, my) && clicked) {
		checked = !checked;
	}
}

bool Checkbox::is_hovered(int mx, int my) const {
	return mx >= x && mx <= x + size && my >= y && my <= y + size;
}

// ============ DROPDOWN ============

Dropdown::Dropdown(int x, int y, const std::vector<std::string>& options)
	: x(x), y(y), options(options), selected(0), open(false) {
}

void Dropdown::render() {
	// Placeholder
}

void Dropdown::handle_mouse(int mx, int my, bool clicked) {
	if (clicked && is_hovered(mx, my)) {
		open = !open;
	}
}

bool Dropdown::is_hovered(int mx, int my) const {
	return mx >= x && mx <= x + 200 && my >= y && my <= y + 30;
}

// ============ UI ============

UI::UI(int screen_width, int screen_height)
	: screen_width(screen_width), screen_height(screen_height) {
}

UI::~UI() {
	for (auto elem : elements) {
		delete elem;
	}
}

void UI::render() {
	for (auto elem : elements) {
		elem->render();
	}
}

void UI::handle_mouse(int x, int y, bool clicked) {
	for (auto elem : elements) {
		elem->handle_mouse(x, y, clicked);
	}
}

Slider* UI::add_slider(int x, int y, int w, int h, float min, float max, float init) {
	Slider* s = new Slider(x, y, w, h, min, max, init);
	elements.push_back(s);
	return s;
}

Button* UI::add_button(int x, int y, int w, int h, const std::string& label) {
	Button* b = new Button(x, y, w, h, label);
	elements.push_back(b);
	return b;
}

Checkbox* UI::add_checkbox(int x, int y, const std::string& label, bool init) {
	Checkbox* c = new Checkbox(x, y, label, init);
	elements.push_back(c);
	return c;
}

Dropdown* UI::add_dropdown(int x, int y, const std::vector<std::string>& options) {
	Dropdown* d = new Dropdown(x, y, options);
	elements.push_back(d);
	return d;
}
