#include "render.h"
#include "../engine/materials.h"
#include <cstring>
#include <cmath>
#include <random>

// ============ SIMPLE CPU RENDERING ============

// CPU render function (simple gradient for demo)
void simple_render(
	float* luminance,
	float* rgb,
	int width,
	int height,
	float time
) {
	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			int pixel_idx = y * width + x;

			// Simple animated gradient
			float u = (float)x / (float)width;
			float v = (float)y / (float)height;

			float r = 0.5f + 0.5f * sinf(u * 3.14159f + time);
			float g = 0.5f + 0.5f * cosf(v * 3.14159f + time);
			float b = 0.5f + 0.5f * sinf((u + v) * 3.14159f + time);

			rgb[pixel_idx * 3 + 0] = std::max(0.0f, std::min(1.0f, r));
			rgb[pixel_idx * 3 + 1] = std::max(0.0f, std::min(1.0f, g));
			rgb[pixel_idx * 3 + 2] = std::max(0.0f, std::min(1.0f, b));

			float lum = 0.299f * r + 0.587f * g + 0.114f * b;
			luminance[pixel_idx] = std::max(0.0f, std::min(1.0f, lum));
		}
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
	  d_materials(nullptr) 
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
	// CPU-based rendering
	simple_render(d_luminance, d_rgb, width, height, time);
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
