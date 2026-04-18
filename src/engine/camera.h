#pragma once

#include <glm/glm.hpp>

class Camera {
public:
	Camera();

	void update(float time);
	void set_position(const glm::vec3& pos);
	void set_target(const glm::vec3& target);
	void set_up(const glm::vec3& up);

	glm::vec3 get_position() const { return position; }
	glm::vec3 get_forward() const { return forward; }
	glm::vec3 get_right() const { return right; }
	glm::vec3 get_up() const { return up; }

	void get_vectors(glm::vec3& out_forward, glm::vec3& out_right, glm::vec3& out_up) const;

	// Орбитальная камера
	void set_orbital_params(float radius, float height, float angle);
	glm::vec3 compute_scene_bounds();
	bool check_collision_camera(const glm::vec3& center, float radius);

private:
	glm::vec3 position;
	glm::vec3 target;
	glm::vec3 forward;
	glm::vec3 right;
	glm::vec3 up;

	float orbital_radius;
	float orbital_height;
	float orbital_angle;
};
