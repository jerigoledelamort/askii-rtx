#include "materials.h"

namespace materials {

Material material_library[8];

void init_materials() {
	// 0 - Matte (матовая поверхность)
	material_library[0].diffuse = 1.0f;
	material_library[0].specular = 0.0f;
	material_library[0].shininess = 1.0f;
	material_library[0].reflectivity = 0.0f;
	material_library[0].roughness = 1.0f;
	material_library[0].refractivity = 0.0f;
	material_library[0].ior = 1.0f;
	material_library[0].absorption = 0.0f;
	material_library[0].r = 0.8f; material_library[0].g = 0.8f; material_library[0].b = 0.8f;

	// 1 - Glossy Plastic (глянцевый пластик)
	material_library[1].diffuse = 0.8f;
	material_library[1].specular = 0.2f;
	material_library[1].shininess = 32.0f;
	material_library[1].reflectivity = 0.1f;
	material_library[1].roughness = 0.3f;
	material_library[1].refractivity = 0.0f;
	material_library[1].ior = 1.0f;
	material_library[1].absorption = 0.0f;
	material_library[1].r = 0.9f; material_library[1].g = 0.2f; material_library[1].b = 0.2f;

	// 2 - Mixed Material
	material_library[2].diffuse = 0.5f;
	material_library[2].specular = 0.5f;
	material_library[2].shininess = 64.0f;
	material_library[2].reflectivity = 0.2f;
	material_library[2].roughness = 0.5f;
	material_library[2].refractivity = 0.0f;
	material_library[2].ior = 1.0f;
	material_library[2].absorption = 0.0f;
	material_library[2].r = 0.2f; material_library[2].g = 0.9f; material_library[2].b = 0.2f;

	// 3 - Glass (стекло)
	material_library[3].diffuse = 0.0f;
	material_library[3].specular = 0.0f;
	material_library[3].shininess = 128.0f;
	material_library[3].reflectivity = 0.1f;
	material_library[3].roughness = 0.05f;
	material_library[3].refractivity = 0.9f;
	material_library[3].ior = 1.5f;
	material_library[3].absorption = 0.05f;
	material_library[3].r = 0.9f; material_library[3].g = 0.9f; material_library[3].b = 0.9f;

	// 4 - Mirror (зеркало)
	material_library[4].diffuse = 0.0f;
	material_library[4].specular = 1.0f;
	material_library[4].shininess = 256.0f;
	material_library[4].reflectivity = 0.95f;
	material_library[4].roughness = 0.02f;
	material_library[4].refractivity = 0.0f;
	material_library[4].ior = 1.0f;
	material_library[4].absorption = 0.0f;
	material_library[4].r = 1.0f; material_library[4].g = 1.0f; material_library[4].b = 1.0f;

	// 5 - Metal (металл)
	material_library[5].diffuse = 0.2f;
	material_library[5].specular = 0.8f;
	material_library[5].shininess = 128.0f;
	material_library[5].reflectivity = 0.8f;
	material_library[5].roughness = 0.2f;
	material_library[5].refractivity = 0.0f;
	material_library[5].ior = 1.0f;
	material_library[5].absorption = 0.0f;
	material_library[5].r = 0.9f; material_library[5].g = 0.8f; material_library[5].b = 0.7f;

	// 6 - Blue Diffuse
	material_library[6].diffuse = 1.0f;
	material_library[6].specular = 0.1f;
	material_library[6].shininess = 8.0f;
	material_library[6].reflectivity = 0.05f;
	material_library[6].roughness = 0.8f;
	material_library[6].refractivity = 0.0f;
	material_library[6].ior = 1.0f;
	material_library[6].absorption = 0.0f;
	material_library[6].r = 0.2f; material_library[6].g = 0.2f; material_library[6].b = 0.9f;

	// 7 - Emissive (светящийся материал)
	material_library[7].diffuse = 0.5f;
	material_library[7].specular = 0.5f;
	material_library[7].shininess = 16.0f;
	material_library[7].reflectivity = 0.3f;
	material_library[7].roughness = 0.6f;
	material_library[7].refractivity = 0.0f;
	material_library[7].ior = 1.0f;
	material_library[7].absorption = 0.0f;
	material_library[7].r = 1.0f; material_library[7].g = 1.0f; material_library[7].b = 0.3f;
}

}  // namespace materials
