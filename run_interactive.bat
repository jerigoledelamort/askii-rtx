@echo off
REM ASCII RTX v1 - Interactive Application Launcher
REM Запуск интерактивного приложения с управлением камерой

cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║         ASCII RTX v1 - Interactive Ray Tracing Engine         ║
echo ║         Real-time camera control and rendering                ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo [INFO] Starting interactive application...
echo.

REM Check if executable exists
if exist "build\ascii_rtx_interactive.exe" (
	echo [OK] Interactive executable found
	echo [RUN] Starting application...
	echo.
	REM Run without pause to allow immediate interaction
	build\ascii_rtx_interactive.exe
	echo.
	echo [DONE] Application closed
) else (
	echo [ERROR] Executable not found!
	echo.
	echo Please build the project first:
	echo   Option 1: Run build.bat all
	echo   Option 2: Run cmake --build .\build --config Release
	echo.
	pause
	exit /b 1
)
