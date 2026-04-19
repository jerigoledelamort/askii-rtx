#pragma once

#include <glm/glm.hpp>

class Camera {
public:
	Camera();

	void update(float time);
	// FPS: позиция + углы Эйлера (pitch, yaw), без орбиты — для GUI
	void sync_fps(const glm::vec3& position, float pitch, float yaw);

	void set_position(const glm::vec3& pos);
	void set_target(const glm::vec3& target);
	void set_up(const glm::vec3& up);

	glm::vec3 get_position() const { return position; }
	glm::vec3 get_forward() const { return forward; }
	glm::vec3 get_right() const { return right; }
	glm::vec3 get_up() const { return up; }
	float get_pitch() const { return pitch_; }
	float get_yaw() const { return yaw_; }

	void get_vectors(glm::vec3& out_forward, glm::vec3& out_right, glm::vec3& out_up) const;

	// Орбитальная камера
	void set_orbital_params(float radius, float height, float angle);
	glm::vec3 compute_scene_bounds();
	bool check_collision_camera(const glm::vec3& center, float radius);

	// FPS: скорости из конфига (вызывать каждый кадр перед move/rotate)
	void set_move_speed(float units_per_second);
	void set_rotate_sensitivity(float radians_per_pixel);

	void move_forward(float dt);
	void move_backward(float dt);
	void move_right(float dt);
	void move_left(float dt);
	void move_up(float dt);
	void move_down(float dt);
	void rotate(float dx, float dy);
	void add_yaw(float delta_yaw_radians);
	// Зум как во Blender: сдвиг вдоль направления взгляда (wheel > 0 — к сцене)
	void dolly_view(float wheel_notches, float world_units_per_notch);

private:
	glm::vec3 position;
	glm::vec3 target;
	glm::vec3 forward;
	glm::vec3 right;
	glm::vec3 up;

	float orbital_radius;
	float orbital_height;
	float orbital_angle;

	// FPS (радианы)
	float yaw_;
	float pitch_;
	float move_speed_;
	float rotate_sens_;

	void rebuild_orientation();
	glm::vec3 planar_forward() const;
	glm::vec3 planar_right() const;
};
