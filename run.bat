@echo off
REM ASCII RTX v1 - Quick Start for Windows
REM Fastest way to run the application

cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║              ASCII RTX v1 - Ray Tracing Engine                ║
echo ║              Rendering 3D in Terminal ASCII Art               ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo [INFO] ASCII RTX v1 - Quick Start
echo.

REM Check if executable exists
if exist "build\ascii_rtx_viewer.exe" (
	echo [OK] Executable found
	echo [RUN] Starting application...
	echo.
	build\ascii_rtx_viewer.exe
	echo.
	echo [DONE] Application finished
	pause
) else (
	echo [ERROR] Executable not found!
	echo.
	echo Please build the project first:
	echo   Option 1: Run build.bat all
	echo   Option 2: Run setup.ps1 -FullBuild
	echo.
	pause
	exit /b 1
)
