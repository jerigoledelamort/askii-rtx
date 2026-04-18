#pragma once

#include <glm/glm.hpp>

namespace lighting {

struct Light {
	glm::vec3 direction;
	float intensity;
};

// Получить направление света
glm::vec3 get_light_direction();

// Отражение компонент
glm::vec3 reflect_vector(const glm::vec3& incident, const glm::vec3& normal);

// Локальное освещение (Phong модель)
glm::vec3 local_lighting(
	const glm::vec3& hit_point,
	const glm::vec3& normal,
	const glm::vec3& view_dir,
	const glm::vec3& albedo,
	float diffuse,
	float specular,
	float shininess,
	float shadow_multiplier
);

}  // namespace lighting
