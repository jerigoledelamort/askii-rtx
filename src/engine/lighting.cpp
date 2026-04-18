#include "lighting.h"
#include "../config/default.h"
#include <glm/gtc/constants.hpp>

namespace lighting {

glm::vec3 get_light_direction() {
	glm::vec3 light(
		config::g_config.light.x,
		config::g_config.light.y,
		config::g_config.light.z
	);
	return glm::normalize(light);
}

glm::vec3 reflect_vector(const glm::vec3& incident, const glm::vec3& normal) {
	return incident - 2.0f * glm::dot(incident, normal) * normal;
}

glm::vec3 local_lighting(
	const glm::vec3& hit_point,
	const glm::vec3& normal,
	const glm::vec3& view_dir,
	const glm::vec3& albedo,
	float diffuse,
	float specular,
	float shininess,
	float shadow_multiplier
) {
	glm::vec3 light_dir = get_light_direction();
	float light_intensity = config::g_config.light.intensity;

	// Ambient
	glm::vec3 ambient = albedo * 0.1f;
	if (!config::g_config.lighting.ambient_enabled) {
		ambient = glm::vec3(0.0f);
	}

	// Diffuse (Lambert)
	float diff = glm::max(0.0f, glm::dot(normal, light_dir));
	glm::vec3 diffuse_component = albedo * diff * diffuse * light_intensity * shadow_multiplier;

	// Specular (Phong)
	glm::vec3 reflect_dir = reflect_vector(-light_dir, normal);
	float spec = glm::pow(glm::max(0.0f, glm::dot(view_dir, reflect_dir)), shininess);
	glm::vec3 specular_component = glm::vec3(spec) * specular * light_intensity * shadow_multiplier;

	return ambient + diffuse_component + specular_component;
}

}  // namespace lighting
