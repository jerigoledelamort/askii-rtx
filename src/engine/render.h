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

private:
	int width, height;

	// GPU буферы
	float* d_luminance;
	float* d_rgb;
	float* d_normal;
	float* d_edge;

	// Временные буферы для TAA
	float* d_accumulation;

	// Scene data
	struct GpuSceneObject {
		int type;
		float px, py, pz;
		float sx, sy, sz;
		int material_id;
	};

	GpuSceneObject* d_scene_objects;
	int num_scene_objects;
	Material* d_materials;
};
