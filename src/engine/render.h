#pragma once

#include <glm/glm.hpp>
#include "../engine/materials.h"

class GpuRender {
public:
	GpuRender(int width, int height);
	~GpuRender();

	// Инициализация GPU ресурсов
	void initialize();

	// Рендеринг кадра
	void render_frame(
		const glm::vec3& camera_pos,
		const glm::vec3& camera_forward,
		const glm::vec3& camera_right,
		const glm::vec3& camera_up,
		float fov,
		int num_samples,
		float time
	);

	// Получить результирующие буферы
	float* get_luminance_buffer() const;
	float* get_rgb_buffer() const;      // RGB values (4 bytes per pixel)
	float* get_normal_buffer() const;   // Normal vectors
	float* get_edge_buffer() const;     // Edge detection

	int get_width() const { return width; }
	int get_height() const { return height; }

	// Сброс temporal accumulation (камера / размер буфера)
	void reset_accumulation_buffer();

	// Данные объекта на CPU (для трассировки); вынесено из private для free-функций в render.cpp
	struct GpuSceneObject {
		int type;
		float px, py, pz;
		float sx, sy, sz;
		int material_id;
	};

private:
	int width, height;

	// GPU буферы
	float* d_luminance;
	float* d_rgb;
	float* d_normal;
	float* d_edge;

	// Накопление сэмплов (float3 на пиксель): sum(rgb) / frame_count → финальный кадр
	float* d_accumulation;

	GpuSceneObject* d_scene_objects;
	int num_scene_objects;
	Material* d_materials;

	glm::vec3 last_camera_pos;
	glm::vec3 last_camera_forward;
	glm::vec3 last_camera_right;
	glm::vec3 last_camera_up;
	unsigned int frame_count;

	void reset_accumulation();
};
