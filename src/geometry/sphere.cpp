#include "sphere.h"

namespace geometry {

float hit_sphere(
	const glm::vec3& ray_origin,
	const glm::vec3& ray_direction,
	const glm::vec3& sphere_center,
	float sphere_radius
) {
	glm::vec3 oc = ray_origin - sphere_center;
	float a = glm::dot(ray_direction, ray_direction);
	float b = 2.0f * glm::dot(oc, ray_direction);
	float c = glm::dot(oc, oc) - sphere_radius * sphere_radius;

	float discriminant = b * b - 4.0f * a * c;
	if (discriminant < 0.0f) {
		return -1.0f;
	}

	float sqrt_disc = glm::sqrt(discriminant);
	float t1 = (-b - sqrt_disc) / (2.0f * a);
	float t2 = (-b + sqrt_disc) / (2.0f * a);

	// Возвращаем ближайшее положительное расстояние
	if (t1 > 0.001f) return t1;
	if (t2 > 0.001f) return t2;
	return -1.0f;
}

glm::vec3 sphere_normal(
	const glm::vec3& hit_point,
	const glm::vec3& sphere_center
) {
	return glm::normalize(hit_point - sphere_center);
}

}  // namespace geometry
