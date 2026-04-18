#include "default.h"

namespace config {

Config g_config;

void init_default_config() {
	// Window
	g_config.window.width = 2560;
	g_config.window.height = 1440;
	g_config.window.fps = 50;

	// Bake
	g_config.bake.num_frames = 300;

	// Temporal AA
	g_config.temporal.enabled = true;
	g_config.temporal.base_alpha = 0.30f;
	g_config.temporal.motion_scale = 1.0f;
	g_config.temporal.base_clamp = 0.05f;

	// Render
	g_config.render.samples = 2;
	g_config.render.exposure = 1.0f;
	g_config.render.gamma = 1.0f;
	g_config.render.diffuse_gi_strength = 0.5f;

	// Font
	g_config.font.size = 10;

	// Performance
	g_config.performance.target_chars = 32000;

	// Camera
	g_config.camera.radius = 2.0f;
	g_config.camera.height = 1.0f;
	g_config.camera.fov = 45.0f;

	// Light
	g_config.light.x = 1.0f;
	g_config.light.y = 1.0f;
	g_config.light.z = 1.0f;
	g_config.light.intensity = 1.0f;

	// Lighting
	g_config.lighting.ambient_enabled = true;
	g_config.lighting.hard_shadows = false;
	g_config.lighting.global_illumination = true;

	// Scene - Default scene setup
	g_config.scene.num_objects = 4;

	// Sphere 1 (center)
	g_config.scene.objects[0].type = 0;  // sphere
	g_config.scene.objects[0].px = 0.0f;
	g_config.scene.objects[0].py = 0.5f;
	g_config.scene.objects[0].pz = 0.0f;
	g_config.scene.objects[0].sx = 0.5f;
	g_config.scene.objects[0].sy = 0.5f;
	g_config.scene.objects[0].sz = 0.5f;
	g_config.scene.objects[0].material_id = 4;  // mirror
	g_config.scene.objects[0].anim_speed = 0.5f;
	g_config.scene.objects[0].anim_phase = 0.0f;

	// Sphere 2 (left)
	g_config.scene.objects[1].type = 0;  // sphere
	g_config.scene.objects[1].px = -1.0f;
	g_config.scene.objects[1].py = 0.3f;
	g_config.scene.objects[1].pz = 0.0f;
	g_config.scene.objects[1].sx = 0.3f;
	g_config.scene.objects[1].sy = 0.3f;
	g_config.scene.objects[1].sz = 0.3f;
	g_config.scene.objects[1].material_id = 3;  // glass
	g_config.scene.objects[1].anim_speed = 0.3f;
	g_config.scene.objects[1].anim_phase = 0.0f;

	// Box (right)
	g_config.scene.objects[2].type = 1;  // box
	g_config.scene.objects[2].px = 1.0f;
	g_config.scene.objects[2].py = 0.3f;
	g_config.scene.objects[2].pz = 0.0f;
	g_config.scene.objects[2].sx = 0.4f;
	g_config.scene.objects[2].sy = 0.4f;
	g_config.scene.objects[2].sz = 0.4f;
	g_config.scene.objects[2].material_id = 1;  // glossy plastic
	g_config.scene.objects[2].anim_speed = 0.2f;
	g_config.scene.objects[2].anim_phase = 0.0f;

	// Plane (floor)
	g_config.scene.objects[3].type = 2;  // plane
	g_config.scene.objects[3].px = 0.0f;
	g_config.scene.objects[3].py = -1.0f;
	g_config.scene.objects[3].pz = 0.0f;
	g_config.scene.objects[3].sx = 1.0f;
	g_config.scene.objects[3].sy = 1.0f;
	g_config.scene.objects[3].sz = 1.0f;
	g_config.scene.objects[3].material_id = 0;  // matte
	g_config.scene.objects[3].anim_speed = 0.0f;
	g_config.scene.objects[3].anim_phase = 0.0f;
}

}  // namespace config
