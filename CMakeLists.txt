cmake_minimum_required(VERSION 3.20)
project(ASCII_RTX LANGUAGES CXX)

# Установка стандартов
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# Флаги компиляции для разных платформ
if(MSVC)
	add_compile_options(/W4 /permissive- /fp:fast /std:c++17)
	add_compile_definitions(UNICODE _UNICODE)
	string(APPEND CMAKE_CXX_FLAGS_RELEASE " /O2 /Oi /Ot")
else()
	add_compile_options(-Wall -Wextra -O3 -std=c++17)
endif()

# CUDA отключена для совместимости - используем CPU версию
# Для полной версии требуется VS 2022 Community (не Insiders)

# Включаемые директории
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/external/glm)
include_directories(${CMAKE_CUDA_TOOLKIT_ROOT_DIR}/include)

# ImGui (опционально)
set(IMGUI_DIR ${CMAKE_CURRENT_SOURCE_DIR}/external/imgui)
if(EXISTS ${IMGUI_DIR})
	include_directories(${IMGUI_DIR})
	include_directories(${IMGUI_DIR}/backends)
	set(IMGUI_FOUND TRUE)
else()
	set(IMGUI_FOUND FALSE)
endif()

# Попытка найти Python (опционально)
find_package(Python3 COMPONENTS Interpreter QUIET)

# Исходные файлы
set(ENGINE_SOURCES
	src/config/default.cpp
	src/engine/core.cpp
	src/engine/render.cpp
	src/engine/camera.cpp
	src/engine/scene.cpp
	src/engine/lighting.cpp
	src/engine/materials.cpp
)

set(GEOMETRY_SOURCES
	src/geometry/sphere.cpp
	src/geometry/box.cpp
	src/geometry/plane.cpp
)

set(PIPELINE_SOURCES
	src/pipeline/video_ascii.cpp
)

set(UTILS_SOURCES
	src/utils/char_calibration.cpp
)

set(UI_SOURCES
	src/apps/viewer/ui.cpp
)

set(MAIN_SOURCES
	src/apps/viewer/main.cpp
)

set(INTERACTIVE_SOURCES
	src/apps/interactive/console_ui.cpp
	src/apps/interactive/input_handler.cpp
	src/apps/interactive/main.cpp
)

set(GUI_SOURCES
	src/apps/gui/app_config.cpp
	src/apps/gui/ascii_renderer.cpp
	src/apps/gui/imgui_setup.cpp
	src/apps/gui/main.cpp
)

# ImGui source files (если найдена библиотека)
if(IMGUI_FOUND)
	set(IMGUI_SOURCES
		${IMGUI_DIR}/imgui.cpp
		${IMGUI_DIR}/imgui_draw.cpp
		${IMGUI_DIR}/imgui_tables.cpp
		${IMGUI_DIR}/imgui_widgets.cpp
		${IMGUI_DIR}/backends/imgui_impl_win32.cpp
		${IMGUI_DIR}/backends/imgui_impl_dx11.cpp
	)
endif()

# Создание статической библиотеки ядра
add_library(ascii_rtx_engine STATIC
	${ENGINE_SOURCES}
	${GEOMETRY_SOURCES}
	${PIPELINE_SOURCES}
	${UTILS_SOURCES}
	${UI_SOURCES}
)

# Ссылки на стандартные библиотеки
target_link_libraries(ascii_rtx_engine 
	${CMAKE_DL_LIBS}
)

# Основное приложение
add_executable(ascii_rtx_viewer ${MAIN_SOURCES})

target_link_libraries(ascii_rtx_viewer 
	ascii_rtx_engine
	${CMAKE_DL_LIBS}
)

# Интерактивное приложение
add_executable(ascii_rtx_interactive ${INTERACTIVE_SOURCES})

target_link_libraries(ascii_rtx_interactive 
	ascii_rtx_engine
	${CMAKE_DL_LIBS}
)

# Настройка целей
set_target_properties(ascii_rtx_viewer PROPERTIES
	CXX_STANDARD 17
	CXX_STANDARD_REQUIRED ON
)

set_target_properties(ascii_rtx_interactive PROPERTIES
	CXX_STANDARD 17
	CXX_STANDARD_REQUIRED ON
)

# GUI приложение (если ImGui найдена)
if(IMGUI_FOUND)
	add_executable(ascii_rtx_gui 
		${GUI_SOURCES}
		${IMGUI_SOURCES}
	)

	target_link_libraries(ascii_rtx_gui 
		ascii_rtx_engine
		d3d11.lib
		d3dcompiler.lib
		${CMAKE_DL_LIBS}
	)

	set_target_properties(ascii_rtx_gui PROPERTIES
		CXX_STANDARD 17
		CXX_STANDARD_REQUIRED ON
		LINK_FLAGS "/SUBSYSTEM:WINDOWS /ENTRY:WinMainCRTStartup"
	)
else()
	message(WARNING "ImGui not found - GUI application will not be built")
endif()

# Информация о конфигурации
message(STATUS "======================================")
message(STATUS "ASCII RTX v1 - Build Configuration")
message(STATUS "======================================")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "======================================")
message(STATUS "Build targets:")
message(STATUS "  - ascii_rtx_engine (static library)")
message(STATUS "  - ascii_rtx_viewer (batch renderer)")
message(STATUS "  - ascii_rtx_interactive (console interactive)")
if(IMGUI_FOUND)
	message(STATUS "  - ascii_rtx_gui (GUI with ImGui)")
else()
	message(STATUS "  - ascii_rtx_gui (SKIPPED - ImGui not found)")
endif()
message(STATUS "======================================")
