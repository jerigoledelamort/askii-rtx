@echo off
REM ASCII RTX v1 - GUI Application Launcher
REM Запуск главного интерактивного приложения с ImGui меню

cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║      ASCII RTX v1 - GUI Application with ImGui Menu           ║
echo ║     Real-time Visualization with Configuration Controls       ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo [INFO] ASCII RTX GUI Application
echo.

REM Check if executable exists
if exist "build\ascii_rtx_gui.exe" (
	echo [OK] GUI executable found
	echo [RUN] Starting application...
	echo.
	build\ascii_rtx_gui.exe
	echo.
	echo [DONE] Application closed
) else (
	echo [ERROR] GUI executable not found!
	echo.
	echo Please build the project first:
	echo   Option 1: Run build.bat all
	echo   Option 2: Run: cmake --build .\build --config Release
	echo.
	pause
	exit /b 1
)

pause
