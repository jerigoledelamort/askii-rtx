#include "box.h"
#include <algorithm>

namespace geometry {

float hit_box(
	const glm::vec3& ray_origin,
	const glm::vec3& ray_direction,
	const glm::vec3& box_min,
	const glm::vec3& box_max
) {
	// Slabs method для AABB пересечения
	glm::vec3 inv_dir = 1.0f / ray_direction;

	float t_min = (box_min.x - ray_origin.x) * inv_dir.x;
	float t_max = (box_max.x - ray_origin.x) * inv_dir.x;
	if (t_min > t_max) std::swap(t_min, t_max);

	float ty_min = (box_min.y - ray_origin.y) * inv_dir.y;
	float ty_max = (box_max.y - ray_origin.y) * inv_dir.y;
	if (ty_min > ty_max) std::swap(ty_min, ty_max);

	if (t_min > ty_max || ty_min > t_max) {
		return -1.0f;
	}

	t_min = glm::max(t_min, ty_min);
	t_max = glm::min(t_max, ty_max);

	float tz_min = (box_min.z - ray_origin.z) * inv_dir.z;
	float tz_max = (box_max.z - ray_origin.z) * inv_dir.z;
	if (tz_min > tz_max) std::swap(tz_min, tz_max);

	if (t_min > tz_max || tz_min > t_max) {
		return -1.0f;
	}

	t_min = glm::max(t_min, tz_min);
	t_max = glm::min(t_max, tz_max);

	if (t_min > 0.001f) return t_min;
	if (t_max > 0.001f) return t_max;
	return -1.0f;
}

glm::vec3 box_normal(
	const glm::vec3& hit_point,
	const glm::vec3& box_min,
	const glm::vec3& box_max
) {
	glm::vec3 center = (box_min + box_max) * 0.5f;
	glm::vec3 half_size = (box_max - box_min) * 0.5f;
	glm::vec3 rel = glm::abs(hit_point - center);

	// Определить какая грань была попадена
	if (rel.x > rel.y && rel.x > rel.z) {
		return glm::vec3(glm::sign(hit_point.x - center.x), 0.0f, 0.0f);
	} else if (rel.y > rel.x && rel.y > rel.z) {
		return glm::vec3(0.0f, glm::sign(hit_point.y - center.y), 0.0f);
	} else {
		return glm::vec3(0.0f, 0.0f, glm::sign(hit_point.z - center.z));
	}
}

}  // namespace geometry
