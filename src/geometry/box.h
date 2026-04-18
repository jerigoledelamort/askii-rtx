#pragma once

#include <glm/glm.hpp>

namespace geometry {

// Пересечение луча с AABB (axis-aligned bounding box)
// Возвращает t (расстояние) или -1 если нет пересечения
float hit_box(
	const glm::vec3& ray_origin,
	const glm::vec3& ray_direction,
	const glm::vec3& box_min,
	const glm::vec3& box_max
);

// Получить нормаль на поверхности коробки
glm::vec3 box_normal(
	const glm::vec3& hit_point,
	const glm::vec3& box_min,
	const glm::vec3& box_max
);

}  // namespace geometry
