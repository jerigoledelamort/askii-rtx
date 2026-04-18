#pragma once

#include "camera.h"
#include "scene.h"
#include "render.h"

class Engine {
public:
	Engine(int width, int height);
	~Engine();

	void initialize();
	void update(float delta_time);
	void render();

	Camera& get_camera() { return camera; }
	Scene& get_scene() { return scene; }
	GpuRender* get_render() { return gpu_render; }

	bool is_running() const { return running; }
	void shutdown() { running = false; }

	float get_elapsed_time() const { return elapsed_time; }

private:
	int width, height;
	bool running;
	float elapsed_time;

	Camera camera;
	Scene scene;
	GpuRender* gpu_render;

	void update_scene();
	void update_camera();
};
