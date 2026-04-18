# ASCII RTX v1 - Build and Run Script (PowerShell)

param(
	[switch]$Clean = $false,
	[switch]$Build = $false,
	[switch]$Run = $false,
	[switch]$All = $false
)

$ErrorActionPreference = "Stop"

# Colors
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Reset = "`e[0m"

function Write-Success {
	Write-Host "$Green✓ $args$Reset"
}

function Write-Info {
	Write-Host "$Yellow[INFO]$Reset $args"
}

function Write-Error-Custom {
	Write-Host "$Red✗ $args$Reset"
}

# Main logic
Write-Info "ASCII RTX v1 - Build Script"

# Check if build directory exists
if ($Clean) {
	Write-Info "Cleaning build directory..."
	if (Test-Path "build") {
		Remove-Item -Recurse -Force "build"
		Write-Success "Build directory cleaned"
	}
}

# Create build directory if not exists
if (-not (Test-Path "build")) {
	Write-Info "Creating build directory..."
	New-Item -ItemType Directory -Path "build" | Out-Null
	Write-Success "Build directory created"
}

# Set up CMake
if ($Build -or $All) {
	Write-Info "Configuring CMake..."

	# Check if CMake is installed
	$cmakePath = (Get-Command cmake -ErrorAction SilentlyContinue).Source
	if (-not $cmakePath) {
		Write-Error-Custom "CMake not found! Please install CMake 3.20+"
		exit 1
	}

	Write-Success "Found CMake: $cmakePath"

	# Run CMake configure
	cd build
	cmake -G "Visual Studio 17 2022" -DCMAKE_CUDA_ARCHITECTURES="75;80" -DCMAKE_BUILD_TYPE=Release ..

	if ($LASTEXITCODE -ne 0) {
		Write-Error-Custom "CMake configuration failed!"
		exit 1
	}
	Write-Success "CMake configuration complete"

	# Build
	Write-Info "Building project..."
	cmake --build . --config Release --parallel 4

	if ($LASTEXITCODE -ne 0) {
		Write-Error-Custom "Build failed!"
		exit 1
	}
	Write-Success "Build complete"

	cd ..
}

# Run
if ($Run -or $All) {
	Write-Info "Running ASCII RTX..."

	$exePath = "build/Release/ascii_rtx_viewer.exe"

	if (-not (Test-Path $exePath)) {
		Write-Error-Custom "Executable not found at $exePath"
		Write-Info "Run with -Build flag first"
		exit 1
	}

	& $exePath
}

# Default: show usage if no arguments
if (-not $Clean -and -not $Build -and -not $Run -and -not $All) {
	Write-Info "Usage:"
	Write-Host "  .\build.ps1 -All          # Clean, build, and run"
	Write-Host "  .\build.ps1 -Build        # Configure and build"
	Write-Host "  .\build.ps1 -Run          # Run existing executable"
	Write-Host "  .\build.ps1 -Clean        # Remove build directory"
	Write-Host "  .\build.ps1 -Build -Run   # Build and run"
}
