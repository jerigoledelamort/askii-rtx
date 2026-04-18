#include "plane.h"

namespace geometry {

float hit_plane(
	const glm::vec3& ray_origin,
	const glm::vec3& ray_direction,
	float plane_y
) {
	if (glm::abs(ray_direction.y) < 0.001f) {
		return -1.0f;
	}

	float t = (plane_y - ray_origin.y) / ray_direction.y;
	if (t > 0.001f) return t;
	return -1.0f;
}

glm::vec3 plane_normal() {
	return glm::vec3(0.0f, 1.0f, 0.0f);
}

}  // namespace geometry
