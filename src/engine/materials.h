#pragma once

struct Material {
	float diffuse;
	float specular;
	float shininess;
	float reflectivity;
	float roughness;
	float refractivity;
	float ior;           // Index of refraction
	float absorption;
	float r, g, b;       // RGB color
};

namespace materials {

// Предопределённые материалы
extern Material material_library[8];

void init_materials();

}  // namespace materials
