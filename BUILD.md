# Build instructions for ASCII RTX v1

## Prerequisites

### Windows
- Visual Studio 2022 or later (with C++ support)
- CUDA Toolkit 11.8 or later
- CMake 3.20 or later
- Python 3.8+ with pip

### Linux
- GCC 9+ or Clang
- CUDA Toolkit 11.8 or later
- CMake 3.20+
- Python 3.8+ with pip

### macOS
- Xcode Command Line Tools
- Note: CUDA support on macOS is limited

## Dependencies

Install Python dependencies:
```bash
pip install numpy imageio pygame
```

## Build Instructions

### Windows (PowerShell)

1. **Create build directory:**
```powershell
mkdir build
cd build
```

2. **Configure CMake:**
```powershell
cmake -G "Visual Studio 17 2022" -DCMAKE_CUDA_ARCHITECTURES=75;80 ..
```

3. **Build the project:**
```powershell
cmake --build . --config Release
```

4. **Run the executable:**
```powershell
.\Release\ascii_rtx_viewer.exe
```

### Linux/macOS

1. **Create build directory:**
```bash
mkdir build
cd build
```

2. **Configure CMake:**
```bash
cmake -DCMAKE_BUILD_TYPE=Release ..
```

3. **Build:**
```bash
cmake --build .
```

4. **Run:**
```bash
./ascii_rtx_viewer
```

## Output

The program will:
1. Initialize the CUDA engine
2. Load the scene with default objects (spheres, cube, plane)
3. Render frames using GPU ray tracing
4. Display frame statistics (FPS, render time)
5. Save RGB data (can be exported to video)

## Controls

- **Real-time mode**: Camera orbits around the scene
- **Parameter adjustment**: Use sliders to modify rendering parameters
- **Resolution selection**: Choose from preset resolutions
- **Save video**: Export rendered frames to MP4

## Performance Tips

1. Reduce `RENDER.samples` for faster preview (2-4 samples)
2. Lower resolution for real-time preview
3. Increase samples for final quality output
4. Enable TAA for smoother temporal results

## Troubleshooting

### CUDA errors
- Ensure NVIDIA GPU driver is up-to-date
- Verify CUDA Toolkit installation
- Check compute capability matches configured architectures

### CMake errors
- Ensure CMake version >= 3.20
- Verify CUDA_TOOLKIT_ROOT_DIR environment variable is set

### Build errors
- Clean build directory: `rm -rf build` (Linux/macOS) or `rmdir /s build` (Windows)
- Rebuild from scratch
- Check compiler version requirements
