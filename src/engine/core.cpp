#include "core.h"
#include "../config/default.h"

Engine::Engine(int w, int h)
	: width(w), height(h), running(true), elapsed_time(0.0f),
	  gpu_render(nullptr) {
}

Engine::~Engine() {
	if (gpu_render) {
		delete gpu_render;
	}
}

void Engine::initialize() {
	config::init_default_config();
	materials::init_materials();

	gpu_render = new GpuRender(width, height);
	gpu_render->initialize();

	scene.init();
	camera.set_orbital_params(
		config::g_config.camera.radius,
		config::g_config.camera.height,
		0.0f
	);
}

void Engine::update(float delta_time) {
	elapsed_time += delta_time;

	update_scene();
	update_camera();
}

void Engine::update_scene() {
	scene.update(elapsed_time);
}

void Engine::update_camera() {
	camera.update(elapsed_time);
}

void Engine::render() {
	glm::vec3 cam_pos = camera.get_position();
	glm::vec3 cam_forward = camera.get_forward();
	glm::vec3 cam_right = camera.get_right();
	glm::vec3 cam_up = camera.get_up();

	gpu_render->render_frame(
		cam_pos, cam_forward, cam_right, cam_up,
		config::g_config.camera.fov,
		config::g_config.render.samples,
		elapsed_time
	);
}
