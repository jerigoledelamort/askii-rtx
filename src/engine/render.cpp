#include "render.h"
#include "../config/default.h"
#include "../geometry/box.h"
#include "../geometry/plane.h"
#include "../geometry/sphere.h"
#include "../engine/materials.h"
#include <cstring>
#include <algorithm>
#include <cmath>

namespace {

constexpr float kHitEpsilon = 0.001f;

struct HitRecord {
	bool hit = false;
	float t = 0.0f;
	glm::vec3 point = glm::vec3(0.0f);
	glm::vec3 normal = glm::vec3(0.0f, 1.0f, 0.0f);
	glm::vec3 albedo = glm::vec3(1.0f);
};

float saturate(float value) {
	return std::max(0.0f, std::min(1.0f, value));
}

glm::vec3 animate_position(const config::SceneObjectConfig& object, float time) {
	glm::vec3 position(object.px, object.py, object.pz);

	if (object.anim_speed > 0.0f) {
		float phase = time * object.anim_speed + object.anim_phase;
		position.y += 0.3f * std::sin(phase * 3.14159f);
	}

	return position;
}

void upload_scene_objects(
	GpuRender::GpuSceneObject* scene_objects,
	int& scene_count,
	float time
) {
	scene_count = config::g_config.scene.num_objects;
	for (int i = 0; i < scene_count; ++i) {
		const auto& source = config::g_config.scene.objects[i];
		glm::vec3 position = animate_position(source, time);

		scene_objects[i].type = source.type;
		scene_objects[i].px = position.x;
		scene_objects[i].py = position.y;
		scene_objects[i].pz = position.z;
		scene_objects[i].sx = source.sx;
		scene_objects[i].sy = source.sy;
		scene_objects[i].sz = source.sz;
		scene_objects[i].material_id = source.material_id;
	}
}

glm::vec3 sky_gradient(const glm::vec3& direction) {
	float t = saturate(0.5f * (direction.y + 1.0f));
	glm::vec3 horizon(0.85f, 0.88f, 0.92f);
	glm::vec3 zenith(0.35f, 0.45f, 0.75f);
	return glm::mix(horizon, zenith, t);
}

bool trace_scene(
	const glm::vec3& ray_origin,
	const glm::vec3& ray_direction,
	const GpuRender::GpuSceneObject* scene_objects,
	int scene_count,
	const Material* materials,
	float max_distance,
	HitRecord& hit
) {
	bool found_hit = false;
	float closest_t = max_distance;

	for (int i = 0; i < scene_count; ++i) {
		const auto& object = scene_objects[i];
		float t = -1.0f;
		glm::vec3 hit_normal(0.0f, 1.0f, 0.0f);

		switch (object.type) {
			case 0: {
				const glm::vec3 center(object.px, object.py, object.pz);
				float radius = std::max(object.sx, std::max(object.sy, object.sz));
				t = geometry::hit_sphere(ray_origin, ray_direction, center, radius);
				if (t > kHitEpsilon) {
					glm::vec3 point = ray_origin + ray_direction * t;
					hit_normal = geometry::sphere_normal(point, center);
				}
				break;
			}
			case 1: {
				const glm::vec3 center(object.px, object.py, object.pz);
				const glm::vec3 half_extent(object.sx, object.sy, object.sz);
				const glm::vec3 box_min = center - half_extent;
				const glm::vec3 box_max = center + half_extent;
				t = geometry::hit_box(ray_origin, ray_direction, box_min, box_max);
				if (t > kHitEpsilon) {
					glm::vec3 point = ray_origin + ray_direction * t;
					hit_normal = geometry::box_normal(point, box_min, box_max);
				}
				break;
			}
			case 2: {
				t = geometry::hit_plane(ray_origin, ray_direction, object.py);
				if (t > kHitEpsilon) {
					hit_normal = geometry::plane_normal();
				}
				break;
			}
			default:
				break;
		}

		if (t > kHitEpsilon && t < closest_t) {
			closest_t = t;
			found_hit = true;

			hit.hit = true;
			hit.t = t;
			hit.point = ray_origin + ray_direction * t;
			hit.normal = hit_normal;

			int material_index = std::clamp(object.material_id, 0, 7);
			const Material& material = materials[material_index];
			hit.albedo = glm::vec3(material.r, material.g, material.b);
		}
	}

	return found_hit;
}

bool camera_changed_significantly(
	const glm::vec3& current,
	const glm::vec3& previous
) {
	glm::vec3 d = current - previous;
	return glm::dot(d, d) > 0.000001f;
}

}

// ============ GPU RENDER CLASS IMPLEMENTATION ============

GpuRender::GpuRender(int w, int h) 
	: width(w), height(h), 
	  d_luminance(nullptr), d_rgb(nullptr),
	  d_normal(nullptr), d_edge(nullptr), 
	  d_accumulation(nullptr),
	  d_scene_objects(nullptr), 
	  num_scene_objects(0), 
	  d_materials(nullptr),
	  last_camera_pos(0.0f),
	  last_camera_forward(0.0f, 0.0f, -1.0f),
	  last_camera_right(1.0f, 0.0f, 0.0f),
	  last_camera_up(0.0f, 1.0f, 0.0f),
	  frame_count(0)
{
}

GpuRender::~GpuRender() {
	if (d_luminance) delete[] d_luminance;
	if (d_rgb) delete[] d_rgb;
	if (d_normal) delete[] d_normal;
	if (d_edge) delete[] d_edge;
	if (d_accumulation) delete[] d_accumulation;
	if (d_scene_objects) delete[] d_scene_objects;
	if (d_materials) delete[] d_materials;
}

void GpuRender::initialize() {
	int total_pixels = width * height;

	// Allocate CPU memory (no GPU available)
	d_luminance = new float[total_pixels];
	d_rgb = new float[total_pixels * 3];
	d_normal = new float[total_pixels * 3];
	d_edge = new float[total_pixels];
	d_accumulation = new float[total_pixels * 3];

	// Allocate scene data
	d_scene_objects = new GpuSceneObject[64];
	d_materials = new Material[8];

	// Copy materials
	memcpy(d_materials, materials::material_library, sizeof(Material) * 8);

	// Initialize buffers
	memset(d_luminance, 0, sizeof(float) * total_pixels);
	memset(d_rgb, 0, sizeof(float) * total_pixels * 3);
	memset(d_normal, 0, sizeof(float) * total_pixels * 3);
	memset(d_edge, 0, sizeof(float) * total_pixels);
	memset(d_accumulation, 0, sizeof(float) * total_pixels * 3);
}

void GpuRender::reset_accumulation() {
	frame_count = 0;
	if (d_accumulation) {
		memset(d_accumulation, 0, sizeof(float) * width * height * 3);
	}
}

void GpuRender::reset_accumulation_buffer() {
	reset_accumulation();
}

void GpuRender::render_frame(
	const glm::vec3& camera_pos,
	const glm::vec3& camera_forward,
	const glm::vec3& camera_right,
	const glm::vec3& camera_up,
	float fov,
	int num_samples,
	float time
) {
	(void)num_samples;

	upload_scene_objects(d_scene_objects, num_scene_objects, time);

	// Без temporal accumulation: один сэмпл на кадр (нет «сглаживания» / шлейфа)
	if (camera_changed_significantly(camera_pos, last_camera_pos) ||
		camera_changed_significantly(camera_forward, last_camera_forward) ||
		camera_changed_significantly(camera_right, last_camera_right) ||
		camera_changed_significantly(camera_up, last_camera_up)) {
		last_camera_pos = camera_pos;
		last_camera_forward = camera_forward;
		last_camera_right = camera_right;
		last_camera_up = camera_up;
	}

	const glm::vec3 light_position(
		config::g_config.light.x,
		config::g_config.light.y,
		config::g_config.light.z
	);
	const float aspect_ratio = static_cast<float>(width) / static_cast<float>(height);
	const float tan_half_fov = std::tan(glm::radians(fov) * 0.5f);

	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			const int pixel_index = y * width + x;
			const int rgb_index = pixel_index * 3;

			const float jitter_x = 0.5f;
			const float jitter_y = 0.5f;

			float ndc_x = ((static_cast<float>(x) + jitter_x) / static_cast<float>(width)) * 2.0f - 1.0f;
			float ndc_y = 1.0f - ((static_cast<float>(y) + jitter_y) / static_cast<float>(height)) * 2.0f;

			glm::vec3 ray_direction = glm::normalize(
				camera_forward +
				ndc_x * aspect_ratio * tan_half_fov * camera_right +
				ndc_y * tan_half_fov * camera_up
			);

			HitRecord hit;
			glm::vec3 sample_color = sky_gradient(ray_direction);
			glm::vec3 sample_normal(0.0f);

			if (trace_scene(
				camera_pos,
				ray_direction,
				d_scene_objects,
				num_scene_objects,
				d_materials,
				1.0e30f,
				hit
			)) {
				const glm::vec3 n = glm::normalize(hit.normal);
				glm::vec3 light_direction = glm::normalize(light_position - hit.point);
				float light_distance = glm::length(light_position - hit.point);

				HitRecord shadow_hit;
				bool occluded = trace_scene(
					hit.point + n * kHitEpsilon,
					light_direction,
					d_scene_objects,
					num_scene_objects,
					d_materials,
					light_distance - 2.0f * kHitEpsilon,
					shadow_hit
				);

				float n_dot_l = std::max(glm::dot(n, light_direction), 0.0f);
				float visibility = occluded ? 0.0f : 1.0f;
				// Lambert: color = albedo * NdotL; hard shadow → direct term 0
				sample_color = glm::clamp(hit.albedo * n_dot_l * visibility, 0.0f, 1.0f);
				sample_normal = n * 0.5f + glm::vec3(0.5f);
				d_edge[pixel_index] = occluded ? 1.0f : 0.0f;
			} else {
				d_edge[pixel_index] = 0.0f;
			}

			const glm::vec3 final_color = sample_color;

			d_rgb[rgb_index + 0] = final_color.r;
			d_rgb[rgb_index + 1] = final_color.g;
			d_rgb[rgb_index + 2] = final_color.b;

			float luminance =
				0.2126f * final_color.r +
				0.7152f * final_color.g +
				0.0722f * final_color.b;
			d_luminance[pixel_index] = saturate(luminance);

			d_normal[rgb_index + 0] = sample_normal.x;
			d_normal[rgb_index + 1] = sample_normal.y;
			d_normal[rgb_index + 2] = sample_normal.z;
		}
	}
}

float* GpuRender::get_luminance_buffer() const {
	return d_luminance;
}

float* GpuRender::get_rgb_buffer() const {
	return d_rgb;
}

float* GpuRender::get_normal_buffer() const {
	return d_normal;
}

float* GpuRender::get_edge_buffer() const {
	return d_edge;
}
