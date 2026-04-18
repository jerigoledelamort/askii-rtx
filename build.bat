@echo off
REM ASCII RTX v1 - Complete Build Script for Windows
REM Usage: build.bat [setup|clean|build|run|all]

setlocal enabledelayedexpansion

if "%1"=="" (
	echo.
	echo ╔════════════════════════════════════════╗
	echo ║     ASCII RTX v1 - Build Script       ║
	echo ║     Ray Tracing in Terminal Art       ║
	echo ╚════════════════════════════════════════╝
	echo.
	echo Usage:
	echo   build.bat setup   - Download dependencies
	echo   build.bat clean   - Remove build artifacts
	echo   build.bat build   - Configure and compile
	echo   build.bat run     - Execute application
	echo   build.bat all     - Setup, clean, build
	echo.
	echo Examples:
	echo   build.bat all              - Full build cycle
	echo   build.bat build ^&^& build.bat run - Build and run
	echo.
	goto end
)

if "%1"=="setup" goto setup
if "%1"=="clean" goto clean
if "%1"=="build" goto build_project
if "%1"=="run" goto run_app
if "%1"=="all" goto all_build

:setup
echo [+] Downloading dependencies...
powershell -ExecutionPolicy Bypass -File ".\download_dependencies.ps1"
if errorlevel 1 goto error
goto end

:clean
echo [+] Cleaning build artifacts...
if exist build rmdir /s /q build
if exist CMakeCache.txt del CMakeCache.txt
echo [*] Clean complete
goto end

:build_project
echo [+] Configuring CMake...
if not exist build mkdir build
cd build

echo [+] Running CMake...
cmake -G "Visual Studio 17 2022" ^
	-DCMAKE_CUDA_ARCHITECTURES="75;80;86;90" ^
	-DCMAKE_BUILD_TYPE=Release ^
	..

if errorlevel 1 (
	echo [!] CMake configuration failed
	cd ..
	goto error
)

echo [+] Building project (this may take a few minutes)...
cmake --build . --config Release --parallel 4
if errorlevel 1 (
	echo [!] Build failed
	cd ..
	goto error
)

cd ..
echo [*] Build complete
goto end

:run_app
echo [+] Starting ASCII RTX v1...
if not exist "build\Release\ascii_rtx_viewer.exe" (
	echo [!] Executable not found. Run 'build.bat build' first
	goto error
)

"build\Release\ascii_rtx_viewer.exe"
goto end

:all_build
call :setup
if errorlevel 1 goto error
call :clean
if errorlevel 1 goto error
call :build_project
if errorlevel 1 goto error
echo.
echo [*] Build successful! Run 'build.bat run' to execute
goto end

:error
echo.
echo [!] Error occurred during build
exit /b 1

:end
