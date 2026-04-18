#pragma once

#include <glm/glm.hpp>

namespace geometry {

// Пересечение луча со сферой
// Возвращает t (расстояние) или -1 если нет пересечения
float hit_sphere(
	const glm::vec3& ray_origin,
	const glm::vec3& ray_direction,
	const glm::vec3& sphere_center,
	float sphere_radius
);

// Получить нормаль на поверхности сферы
glm::vec3 sphere_normal(
	const glm::vec3& hit_point,
	const glm::vec3& sphere_center
);

}  // namespace geometry
