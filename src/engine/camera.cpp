#include "camera.h"
#include "../config/default.h"
#include <glm/gtc/constants.hpp>
#include <cmath>

Camera::Camera()
	: position(0.0f, 0.0f, 0.0f),
	  target(0.0f, 0.0f, 0.0f),
	  forward(0.0f, 0.0f, -1.0f),
	  right(1.0f, 0.0f, 0.0f),
	  up(0.0f, 1.0f, 0.0f),
	  orbital_radius(config::g_config.camera.radius),
	  orbital_height(config::g_config.camera.height),
	  orbital_angle(0.0f)
{
}

void Camera::update(float time) {
	orbital_angle += 0.5f * time;  // Медленное вращение вокруг центра

	float x = orbital_radius * std::cos(orbital_angle);
	float z = orbital_radius * std::sin(orbital_angle);
	float y = orbital_height;

	position = glm::vec3(x, y, z);
	target = glm::vec3(0.0f, 0.5f, 0.0f);

	forward = glm::normalize(target - position);
	right = glm::normalize(glm::cross(forward, glm::vec3(0.0f, 1.0f, 0.0f)));
	up = glm::normalize(glm::cross(right, forward));
}

void Camera::set_position(const glm::vec3& pos) {
	position = pos;
}

void Camera::set_target(const glm::vec3& t) {
	target = t;
	forward = glm::normalize(target - position);
}

void Camera::set_up(const glm::vec3& u) {
	up = glm::normalize(u);
}

void Camera::get_vectors(glm::vec3& out_forward, glm::vec3& out_right, glm::vec3& out_up) const {
	out_forward = forward;
	out_right = right;
	out_up = up;
}

void Camera::set_orbital_params(float radius, float height, float angle) {
	orbital_radius = radius;
	orbital_height = height;
	orbital_angle = angle;
}

glm::vec3 Camera::compute_scene_bounds() {
	// Примитивная оценка границ сцены
	float max_extent = 3.0f;
	return glm::vec3(max_extent, max_extent, max_extent);
}

bool Camera::check_collision_camera(const glm::vec3& center, float radius) {
	float dist = glm::distance(position, center);
	return dist < radius + 0.5f;  // Некоторый margin
}
