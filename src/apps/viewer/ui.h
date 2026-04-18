#pragma once

#include <glm/glm.hpp>
#include <string>
#include <vector>

class UIElement {
public:
	virtual ~UIElement() = default;
	virtual void render() = 0;
	virtual void handle_mouse(int x, int y, bool clicked) = 0;
	virtual bool is_hovered(int x, int y) const = 0;
};

class Slider : public UIElement {
public:
	Slider(int x, int y, int width, int height, float min_val, float max_val, float initial);

	void render() override;
	void handle_mouse(int x, int y, bool clicked) override;
	bool is_hovered(int x, int y) const override;

	float get_value() const { return value; }
	void set_value(float v) { value = v; }

private:
	int x, y, width, height;
	float min_value, max_value;
	float value;
	bool dragging;
};

class Button : public UIElement {
public:
	Button(int x, int y, int width, int height, const std::string& label);

	void render() override;
	void handle_mouse(int x, int y, bool clicked) override;
	bool is_hovered(int x, int y) const override;

	bool was_pressed() const { return pressed; }
	void reset_pressed() { pressed = false; }

private:
	int x, y, width, height;
	std::string label;
	bool pressed;
	bool hovered;
};

class Checkbox : public UIElement {
public:
	Checkbox(int x, int y, const std::string& label, bool initial);

	void render() override;
	void handle_mouse(int x, int y, bool clicked) override;
	bool is_hovered(int x, int y) const override;

	bool is_checked() const { return checked; }
	void set_checked(bool c) { checked = c; }

private:
	int x, y;
	int size;
	std::string label;
	bool checked;
};

class Dropdown : public UIElement {
public:
	Dropdown(int x, int y, const std::vector<std::string>& options);

	void render() override;
	void handle_mouse(int x, int y, bool clicked) override;
	bool is_hovered(int x, int y) const override;

	int get_selected() const { return selected; }
	void set_selected(int s) { selected = s; }

private:
	int x, y;
	std::vector<std::string> options;
	int selected;
	bool open;
};

class UI {
public:
	UI(int screen_width, int screen_height);
	~UI();

	void render();
	void handle_mouse(int x, int y, bool clicked);

	// Element accessors
	Slider* add_slider(int x, int y, int w, int h, float min, float max, float init);
	Button* add_button(int x, int y, int w, int h, const std::string& label);
	Checkbox* add_checkbox(int x, int y, const std::string& label, bool init);
	Dropdown* add_dropdown(int x, int y, const std::vector<std::string>& options);

private:
	int screen_width, screen_height;
	std::vector<UIElement*> elements;
};
