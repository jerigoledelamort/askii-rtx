#!/usr/bin/env powershell

# ASCII RTX v1 - Setup and Build Script for Windows

param(
	[switch]$Setup = $false,
	[switch]$Clean = $false,
	[switch]$Build = $false,
	[switch]$Run = $false,
	[switch]$FullBuild = $false
)

$ErrorActionPreference = "Stop"

# ============ COLORS ============
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[36m"
$Reset = "`e[0m"

function Write-Success {
	Write-Host "$Green[✓]$Reset $args"
}

function Write-Info {
	Write-Host "$Blue[i]$Reset $args"
}

function Write-Warning {
	Write-Host "$Yellow[!]$Reset $args"
}

function Write-Error-Msg {
	Write-Host "$Red[✗]$Reset $args"
}

# ============ SETUP ============
function Setup-Dependencies {
	Write-Info "Setting up dependencies..."

	# Check Python
	Write-Info "Checking Python installation..."
	$python = Get-Command python -ErrorAction SilentlyContinue
	if (-not $python) {
		Write-Error-Msg "Python not found! Please install Python 3.8+"
		Write-Info "Download from: https://www.python.org/downloads/"
		exit 1
	}
	Write-Success "Python found: $(python --version)"

	# Check CUDA
	Write-Info "Checking CUDA Toolkit..."
	$nvcc = Get-Command nvcc -ErrorAction SilentlyContinue
	if (-not $nvcc) {
		Write-Warning "CUDA Toolkit not found in PATH"
		Write-Info "Please install from: https://developer.nvidia.com/cuda-downloads"
		Write-Info "And add CUDA/bin to your PATH"
	} else {
		Write-Success "CUDA found: $(nvcc --version | Select-Object -First 1)"
	}

	# Check CMake
	Write-Info "Checking CMake..."
	$cmake = Get-Command cmake -ErrorAction SilentlyContinue
	if (-not $cmake) {
		Write-Error-Msg "CMake not found! Installing via Chocolatey..."
		choco install cmake -y
	} else {
		Write-Success "CMake found: $(cmake --version | Select-Object -First 1)"
	}

	# Install Python packages
	Write-Info "Installing Python packages..."
	python -m pip install --upgrade pip
	python -m pip install numpy imageio pygame
	Write-Success "Python packages installed"

	Write-Success "Dependencies setup complete!"
}

# ============ CLEAN ============
function Clean-Build {
	Write-Info "Cleaning build artifacts..."

	if (Test-Path "build") {
		Remove-Item -Recurse -Force "build"
		Write-Success "Build directory removed"
	}

	if (Test-Path "CMakeCache.txt") {
		Remove-Item -Force "CMakeCache.txt"
	}

	Write-Success "Clean complete!"
}

# ============ BUILD ============
function Invoke-CMakeBuild {
	Write-Info "Building project..."

	# Create build directory
	if (-not (Test-Path "build")) {
		New-Item -ItemType Directory -Path "build" | Out-Null
		Write-Success "Build directory created"
	}

	# Enter build directory
	Push-Location "build"

	# Run CMake configure
	Write-Info "Running CMake configuration..."
	cmake -G "Visual Studio 17 2022" `
		  -DCMAKE_CUDA_ARCHITECTURES="75;80;86;90" `
		  -DCMAKE_BUILD_TYPE=Release `
		  ..

	if ($LASTEXITCODE -ne 0) {
		Write-Error-Msg "CMake configuration failed!"
		Pop-Location
		exit 1
	}
	Write-Success "CMake configuration complete"

	# Build
	Write-Info "Compiling (this may take a few minutes)..."
	cmake --build . --config Release --parallel 4

	if ($LASTEXITCODE -ne 0) {
		Write-Error-Msg "Build failed!"
		Pop-Location
		exit 1
	}
	Write-Success "Build complete!"

	Pop-Location
}

# ============ RUN ============
function Invoke-Application {
	Write-Info "Starting ASCII RTX v1..."

	$exePath = "build/Release/ascii_rtx_viewer.exe"

	if (-not (Test-Path $exePath)) {
		Write-Error-Msg "Executable not found at: $exePath"
		Write-Info "Run with -Build flag first"
		exit 1
	}

	Write-Success "Launching application..."
	& $exePath
}

# ============ MAIN ============
Write-Host "$Blue╔════════════════════════════════════════╗$Reset"
Write-Host "$Blue║     ASCII RTX v1 - Build System       ║$Reset"
Write-Host "$Blue║     Ray Tracing in Terminal Art       ║$Reset"
Write-Host "$Blue╚════════════════════════════════════════╝$Reset"
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

if ($Setup) {
	Setup-Dependencies
}

if ($Clean) {
	Clean-Build
}

if ($Build) {
	Invoke-CMakeBuild
}

if ($Run) {
	Invoke-Application
}

if ($FullBuild) {
	Write-Info "Running full build cycle..."
	Setup-Dependencies
	Clean-Build
	Invoke-CMakeBuild
	Write-Success "Build successful! Run with -Run flag to execute"
}

if (-not $Setup -and -not $Clean -and -not $Build -and -not $Run -and -not $FullBuild) {
	Write-Info "Usage:"
	Write-Host ""
	Write-Host "  .\setup.ps1 -FullBuild  # Setup dependencies, clean, build"
	Write-Host "  .\setup.ps1 -Setup      # Install dependencies"
	Write-Host "  .\setup.ps1 -Build      # Configure and compile"
	Write-Host "  .\setup.ps1 -Run        # Execute"
	Write-Host "  .\setup.ps1 -Clean      # Remove build files"
	Write-Host ""
	Write-Host "Examples:"
	Write-Host "  .\setup.ps1 -Setup -Build -Run  # Full setup and run"
	Write-Host "  .\setup.ps1 -FullBuild          # Complete build (no run)"
	Write-Host ""
}

Write-Success "Done!"
