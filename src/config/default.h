#pragma once

namespace config {

// ============ WINDOW ============
struct WindowConfig {
	int width = 2560;
	int height = 1440;
	int fps = 50;
	const char* title = "ASCII RTX v1 - Ray Tracing Engine";
};

// ============ BAKE ============
struct BakeConfig {
	int num_frames = 300;  // Количество кадров для рендеринга
};

// ============ TEMPORAL AA ============
struct TemporalConfig {
	bool enabled = true;
	float base_alpha = 0.30f;      // Вес текущего кадра
	float motion_scale = 1.0f;     // Масштабирование движения
	float base_clamp = 0.05f;      // Ограничение контрастности
};

// ============ RENDER ============
struct RenderConfig {
	const char* chars = " .,:-~=+*#%@";
	int samples = 2;              // Сэмплы на пиксель
	float exposure = 1.0f;
	float gamma = 1.0f;
	float diffuse_gi_strength = 0.5f;
};

// ============ FONT ============
struct FontConfig {
	const char* name = "Consolas";
	int size = 10;
};

// ============ PERFORMANCE ============
struct PerformanceConfig {
	int target_chars = 32000;  // Целевое количество символов на экран
};

// ============ CAMERA ============
struct CameraConfig {
	float radius = 2.0f;
	float height = 1.0f;
	float fov = 45.0f;
};

// ============ LIGHT ============
struct LightConfig {
	float x = 1.0f;
	float y = 1.0f;
	float z = 1.0f;
	float intensity = 1.0f;
};

// ============ LIGHTING FLAGS ============
struct LightingFlagsConfig {
	bool ambient_enabled = true;
	bool hard_shadows = false;
	bool global_illumination = true;
};

// ============ SCENE OBJECT ============
struct SceneObjectConfig {
	int type;           // 0=sphere, 1=box, 2=plane
	float px, py, pz;   // position
	float sx, sy, sz;   // scale
	int material_id;
	float anim_speed;
	float anim_phase;
};

// ============ SCENE ============
struct SceneConfig {
	SceneObjectConfig objects[64];
	int num_objects;
};

// ============ GLOBAL CONFIG ============
struct Config {
	WindowConfig window;
	BakeConfig bake;
	TemporalConfig temporal;
	RenderConfig render;
	FontConfig font;
	PerformanceConfig performance;
	CameraConfig camera;
	LightConfig light;
	LightingFlagsConfig lighting;
	SceneConfig scene;
};

// Глобальный конфиг
extern Config g_config;

// Инициализация конфига по умолчанию
void init_default_config();

}  // namespace config
