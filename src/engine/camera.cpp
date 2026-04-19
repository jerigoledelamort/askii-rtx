#include "camera.h"
#include "../config/default.h"
#include <glm/gtc/constants.hpp>
#include <algorithm>
#include <cmath>

namespace {

constexpr float kPitchLimitRad = glm::radians(89.0f);

} // namespace

Camera::Camera()
	: position(0.0f, 0.0f, 0.0f),
	  target(0.0f, 0.0f, 0.0f),
	  forward(0.0f, 0.0f, -1.0f),
	  right(1.0f, 0.0f, 0.0f),
	  up(0.0f, 1.0f, 0.0f),
	  orbital_radius(config::g_config.camera.radius),
	  orbital_height(config::g_config.camera.height),
	  orbital_angle(0.0f),
	  yaw_(0.0f),
	  pitch_(0.0f),
	  move_speed_(1.0f),
	  rotate_sens_(0.0025f)
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

void Camera::rebuild_orientation() {
	pitch_ = std::clamp(pitch_, -kPitchLimitRad, kPitchLimitRad);

	forward = glm::normalize(glm::vec3(
		std::sin(yaw_) * std::cos(pitch_),
		std::sin(pitch_),
		-std::cos(yaw_) * std::cos(pitch_)
	));

	const glm::vec3 world_up(0.0f, 1.0f, 0.0f);
	right = glm::normalize(glm::cross(forward, world_up));
	if (glm::dot(right, right) < 1.0e-6f) {
		right = glm::vec3(1.0f, 0.0f, 0.0f);
	}
	up = glm::normalize(glm::cross(right, forward));
	target = position + forward;
}

void Camera::sync_fps(const glm::vec3& pos, float pitch, float yaw) {
	position = pos;
	pitch_ = pitch;
	yaw_ = yaw;
	rebuild_orientation();
}

void Camera::set_move_speed(float units_per_second) {
	move_speed_ = std::max(0.0f, units_per_second);
}

void Camera::set_rotate_sensitivity(float radians_per_pixel) {
	rotate_sens_ = std::max(0.0f, radians_per_pixel);
}

glm::vec3 Camera::planar_forward() const {
	glm::vec3 f(forward.x, 0.0f, forward.z);
	const float len2 = glm::dot(f, f);
	if (len2 < 1.0e-8f) {
		return glm::vec3(0.0f, 0.0f, -1.0f);
	}
	return glm::normalize(f);
}

glm::vec3 Camera::planar_right() const {
	const glm::vec3 pf = planar_forward();
	const glm::vec3 world_up(0.0f, 1.0f, 0.0f);
	return glm::normalize(glm::cross(pf, world_up));
}

void Camera::move_forward(float dt) {
	position += planar_forward() * move_speed_ * dt;
	target = position + forward;
}

void Camera::move_backward(float dt) {
	position -= planar_forward() * move_speed_ * dt;
	target = position + forward;
}

void Camera::move_right(float dt) {
	position += planar_right() * move_speed_ * dt;
	target = position + forward;
}

void Camera::move_left(float dt) {
	position -= planar_right() * move_speed_ * dt;
	target = position + forward;
}

void Camera::move_up(float dt) {
	const glm::vec3 world_up(0.0f, 1.0f, 0.0f);
	position += world_up * move_speed_ * dt;
	target = position + forward;
}

void Camera::move_down(float dt) {
	const glm::vec3 world_up(0.0f, 1.0f, 0.0f);
	position -= world_up * move_speed_ * dt;
	target = position + forward;
}

void Camera::rotate(float dx, float dy) {
	yaw_ += dx * rotate_sens_;
	// Инверсия по вертикали: движение мыши вверх — взгляд вверх
	pitch_ -= dy * rotate_sens_;
	rebuild_orientation();
}

void Camera::add_yaw(float delta_yaw_radians) {
	yaw_ += delta_yaw_radians;
	rebuild_orientation();
}

void Camera::dolly_view(float wheel_notches, float world_units_per_notch) {
	if (std::fabs(wheel_notches) < 1.0e-8f) {
		return;
	}
	position += forward * (wheel_notches * world_units_per_notch);
	target = position + forward;
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
	float max_extent = 3.0f;
	return glm::vec3(max_extent, max_extent, max_extent);
}

bool Camera::check_collision_camera(const glm::vec3& center, float radius) {
	float dist = glm::distance(position, center);
	return dist < radius + 0.5f;
}
