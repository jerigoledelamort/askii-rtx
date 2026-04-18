#pragma once

#include <glm/glm.hpp>

namespace geometry {

// Пересечение луча с горизонтальной плоскостью
float hit_plane(
	const glm::vec3& ray_origin,
	const glm::vec3& ray_direction,
	float plane_y
);

// Нормаль плоскости
glm::vec3 plane_normal();

}  // namespace geometry
