# ASCII RTX v1 - Ray Tracing Engine

Advanced graphics engine for rendering 3D scenes in ASCII art using GPU ray tracing, global illumination, and CUDA acceleration.

## Features

- **GPU Ray Tracing** - CUDA-accelerated ray tracing on NVIDIA GPUs
- **Global Illumination** - Realistic indirect lighting simulation
- **Temporal Anti-Aliasing** - Smooth temporal filtering between frames
- **Multiple Primitives** - Support for spheres, boxes, and planes
- **Material System** - Diffuse, glossy, reflective, and refractive materials
- **Interactive UI** - Real-time parameter adjustment via sliders and controls
- **Video Export** - Export rendered frames to MP4 format
- **Cross-Platform** - Windows, Linux, macOS support

## Architecture

### Core Modules

- **engine/** - GPU rendering pipeline
  - `core.cpp/h` - Main engine coordination
  - `render.cu` - CUDA kernels for ray tracing
  - `camera.cpp/h` - Camera system and orbital control
  - `scene.cpp/h` - Scene management
  - `lighting.cpp/h` - Illumination models
  - `materials.cpp/h` - Material properties

- **geometry/** - Geometric primitives
  - `sphere.cpp/h` - Ray-sphere intersection
  - `box.cpp/h` - AABB ray intersection
  - `plane.cpp/h` - Plane intersection

- **pipeline/** - Post-processing
  - `video_ascii.cpp/h` - Video export

- **apps/viewer/** - Main application
  - `main.cpp/h` - Main render loop
  - `ui.cpp/h` - UI elements (sliders, buttons, etc.)

- **utils/** - Utilities
  - `char_calibration.cpp/h` - ASCII character brightness mapping

- **config/** - Configuration
  - `default.cpp/h` - Default configuration and settings

## Quick Start

### Windows (PowerShell)

```powershell
# Clone or navigate to project
cd D:\Projects\askii-rtx-ver6

# Run build script (builds and executes)
.\build.ps1 -All

# Or step-by-step:
.\build.ps1 -Build  # Just build
.\build.ps1 -Run    # Just run
```

### Linux/macOS

```bash
cd /path/to/ascii-rtx-ver6

# Create and enter build directory
mkdir build
cd build

# Configure with CMake
cmake -DCMAKE_BUILD_TYPE=Release ..

# Build
cmake --build . --parallel 4

# Run
./ascii_rtx_viewer
```

## Configuration

Edit `src/config/default.h` to customize:

- **Resolution**: Window width/height and target character count
- **Rendering**: Ray samples, exposure, gamma, GI strength
- **Camera**: Orbital radius, height, FOV
- **Lighting**: Light direction, intensity, shadow options
- **Scene**: Add/modify objects (spheres, boxes, planes)

Example modification in `default.cpp`:

```cpp
void init_default_config() {
	g_config.window.width = 2560;      // Increase resolution
	g_config.render.samples = 4;       // More samples for quality
	g_config.render.exposure = 1.2f;   // Brighten image
}
```

## Building

See [BUILD.md](BUILD.md) for detailed build instructions.

### Requirements

- **C++17 compiler** (MSVC, GCC, or Clang)
- **CUDA Toolkit 11.8+** with curand, cudart
- **CMake 3.20+**
- **Python 3.8+** (for utilities)

### Build Process

```bash
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --config Release
```

## Usage

### Real-Time Mode

```
./ascii_rtx_viewer
```

The viewer will:
1. Initialize GPU resources
2. Load default scene (sphere, cube, plane)
3. Start rendering with orbiting camera
4. Display FPS counter and frame statistics
5. Stream ASCII output to console

### Command Line Options

```
--resolution [1280x720|1920x1080|2560x1440]   Set render resolution
--samples [1|2|4|8]                            Ray samples per pixel
--fps [30|50|60]                                Target frames per second
--export output.mp4                            Export to video file
```

## Performance Optimization

### Tips for Better Performance

1. **Reduce samples** for preview mode (2 samples minimum)
2. **Lower resolution** for real-time feedback
3. **Enable TAA** for temporal smoothing
4. **Use simpler scenes** for interactive adjustment
5. **Increase samples** (4-16) for final quality render

### GPU Utilization

The renderer automatically adjusts to your GPU:
- **RTX 3060** and above: Optimal performance
- **GTX 1060** and similar: Reduced samples recommended
- **Older cards**: Lower resolution and samples

## Advanced Usage

### Custom Scenes

Edit `default.cpp` to add objects:

```cpp
// Add a reflective sphere
g_config.scene.objects[0].type = 0;           // Sphere
g_config.scene.objects[0].px = 1.5f;          // X position
g_config.scene.objects[0].py = 0.5f;          // Y position
g_config.scene.objects[0].pz = 0.0f;          // Z position
g_config.scene.objects[0].sx = 0.4f;          // Radius
g_config.scene.objects[0].material_id = 4;    // Mirror material
```

### Custom Materials

Modify `materials.cpp`:

```cpp
// Material properties
material_library[5].diffuse = 0.5f;      // Diffuse coefficient
material_library[5].specular = 0.8f;     // Specular coefficient
material_library[5].shininess = 64.0f;   // Specular exponent
material_library[5].r = 0.8f;            // Red
material_library[5].g = 0.2f;            // Green
material_library[5].b = 0.2f;            // Blue
```

### Export to Video

```cpp
VideoExporter exporter(1920, 1080, 60, "output.mp4");

for (int frame = 0; frame < 300; ++frame) {
	engine.render();
	float* rgb = engine.get_render()->get_rgb_buffer();
	exporter.add_frame(rgb);
}

exporter.finish();
```

## Troubleshooting

### Build Errors

**CMake configuration fails:**
```powershell
# Ensure Visual Studio build tools are installed
cmake --version  # Check CMake version (need 3.20+)
```

**CUDA compilation error:**
```powershell
# Verify CUDA is installed
nvcc --version

# Set CUDA path if needed
$env:CUDA_PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0"
```

### Runtime Issues

**"CUDA out of memory":**
- Reduce resolution or sample count
- Close other GPU-intensive applications

**"No GPU detected":**
- Check NVIDIA driver version
- Run `nvidia-smi` to verify GPU

**Slow rendering:**
- Start with `--samples 2` for quick preview
- Increase for final render

## Architecture Diagram

```
┌─────────────────────────────────────┐
│  Main Application (main.cpp)        │
│  - Window & event handling          │
│  - UI management                    │
└──────────────┬──────────────────────┘
			   │
┌──────────────▼──────────────────────┐
│  Engine Core (core.h)               │
│  - Scene/Camera coordination        │
│  - Frame synchronization            │
└──────────────┬──────────────────────┘
			   │
	 ┌─────────┴──────────┬────────────┐
	 │                    │            │
┌────▼────┐       ┌──────▼──┐   ┌─────▼─────┐
│ Camera  │       │  Scene  │   │ GPU Render│
│ Control │       │ Objects │   │ (CUDA)    │
└─────────┘       └─────────┘   └────┬──────┘
									 │
					┌────────────────┼────────────────┐
					│                │                │
			┌───────▼───┐    ┌──────▼──┐    ┌────────▼──┐
			│  Geometry │    │Materials│    │ Lighting  │
			│(Sphere,   │    │(8 types)│    │  Models   │
			│ Box,      │    │         │    │(Phong)    │
			│ Plane)    │    │         │    │           │
			└───────────┘    └─────────┘    └───────────┘
					│
					│ Ray Tracing
					│
			┌───────▼──────┐
			│RGB/Luminance │
			│  Buffers     │
			└───────┬──────┘
					│
			┌───────▼──────┐
			│ Post-Process │
			│ (TAA, Gamma) │
			└───────┬──────┘
					│
			┌───────▼──────┐
			│ ASCII Render │
			│ (char map)   │
			└───────┬──────┘
					│
			┌───────▼──────┐
			│ Display/File │
			│  Output      │
			└──────────────┘
```

## Performance Metrics

Typical performance on modern hardware:

| Hardware | Resolution | Samples | FPS |
|----------|-----------|---------|-----|
| RTX 4070 | 1280x720  | 2       | 60+ |
| RTX 3070 | 1920x1080 | 4       | 30+ |
| RTX 2080 | 1920x1080 | 2       | 25  |
| GTX 1070 | 1280x720  | 2       | 15  |

## Known Limitations

- Volumetric effects not supported
- No dynamic geometry (topology doesn't change)
- Limited to static scenes (pre-animated objects only)
- ASCII output resolution limited by terminal
- CUDA only (no OpenCL or other GPU APIs)

## Future Enhancements

- [ ] Path tracing for higher quality
- [ ] Mesh loading (OBJ/FBX)
- [ ] Procedural texture generation
- [ ] Motion blur
- [ ] Depth of field
- [ ] Photon mapping for caustics
- [ ] GPU-accelerated video encoding
- [ ] Network rendering support

## License

This project is provided as-is for educational purposes.

## Author

ASCII RTX Development Team

## References

- [NVIDIA CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)
- [Ray Tracing Fundamentals](https://www.scratchapixel.com/)
- [GPU Rendering Optimization](https://developer.nvidia.com/blog/)

---

**Questions or issues?** Check [BUILD.md](BUILD.md) or review the source code comments.
