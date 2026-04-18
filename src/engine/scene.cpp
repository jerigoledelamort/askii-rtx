#include "scene.h"
#include "../config/default.h"
#include <cmath>

Scene::Scene() : num_objects(0) {
}

Scene::~Scene() {
}

void Scene::init() {
	num_objects = config::g_config.scene.num_objects;
	for (int i = 0; i < num_objects; ++i) {
		const auto& cfg = config::g_config.scene.objects[i];
		objects[i].type = cfg.type;
		objects[i].position = glm::vec3(cfg.px, cfg.py, cfg.pz);
		objects[i].scale = glm::vec3(cfg.sx, cfg.sy, cfg.sz);
		objects[i].material_id = cfg.material_id;
		objects[i].anim_speed = cfg.anim_speed;
		objects[i].anim_phase = cfg.anim_phase;
	}
}

void Scene::update(float time) {
	for (int i = 0; i < num_objects; ++i) {
		apply_animation(i, time);
	}
}

void Scene::transform_vertices() {
	// В этом примитивном движке трансформации пока что статичные
}

void Scene::compute_vertex_normals() {
	// Нормали вычисляются прямо в CUDA для примитивов
}

void Scene::apply_animation(int index, float time) {
	if (index < 0 || index >= num_objects) return;

	SceneObject& obj = objects[index];
	float anim_time = time * obj.anim_speed;

	// Простая анимация: вверх-вниз
	if (obj.anim_speed > 0.0f) {
		float oscillation = 0.3f * std::sin(anim_time * 3.14159f);
		obj.position.y += oscillation;
	}
}

int Scene::get_num_objects() const {
	return num_objects;
}

const Scene::SceneObject* Scene::get_objects() const {
	return objects;
}
