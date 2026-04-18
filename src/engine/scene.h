#pragma once

#include <glm/glm.hpp>

class Scene {
public:
	Scene();
	~Scene();

	void init();
	void update(float time);
	void transform_vertices();
	void compute_vertex_normals();

	// Getters для CUDA
	int get_num_objects() const;
	struct SceneObject {
		int type;  // 0=sphere, 1=box, 2=plane
		glm::vec3 position;
		glm::vec3 scale;
		int material_id;
		float anim_speed;
		float anim_phase;
	};

	const SceneObject* get_objects() const;

private:
	SceneObject objects[64];
	int num_objects;

	void apply_animation(int index, float time);
};
