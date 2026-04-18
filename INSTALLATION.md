# ASCII RTX v1 - Installation & Usage Guide

## ✅ Проект готов к использованию!

ASCII RTX v1 был **успешно скомпилирован** и создан исполняемый файл.

```
Компилятор:  MSVC 19.51 (Visual Studio 2026 Insiders)
Разрешение:  Release (оптимизировано)
Файл:        .\build\ascii_rtx_viewer.exe (37.9 KB)
Библиотека:  .\build\ascii_rtx_engine.lib (281.2 KB)
Производ-ть: ~71 FPS на среднем оборудовании
```

---

## 🚀 Быстрый старт (30 секунд)

### Самый быстрый способ - просто запустить:

```batch
.\run.bat
```

Или напрямую:

```batch
.\build\ascii_rtx_viewer.exe
```

Приложение начнёт рендеринг 500 кадров и покажет статистику.

---

## 📦 Полная инструкция по установке

### Требования

- **Windows 10/11** или **Linux/macOS** (с установленными build tools)
- **CMake 3.20+** (установлен ✅)
- **C++17 компилятор** (MSVC, GCC, или Clang)
- **Python 3.8+** (опционально, для будущих расширений)

### Шаг 1: Скачать проект

```powershell
# Проект уже находится в:
cd D:\Projects\askii-rtx-ver6
```

### Шаг 2: Скачать зависимости (первый раз)

```powershell
# Скачать GLM математическую библиотеку
.\download_deps.ps1

# Проверить что всё установлено:
Test-Path ".\external\glm\glm\glm.hpp"  # Должно вывести True
```

### Шаг 3: Сборка проекта

#### Вариант A: Автоматическая (рекомендуется)

```batch
# Использовать batch скрипт для Windows
build.bat all
```

#### Вариант B: Через CMake вручную

```powershell
# Создать директорию сборки
mkdir build
cd build

# Конфигурировать CMake
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release ..

# Компилировать
cmake --build . --config Release --parallel 4

# Вернуться в корневую директорию
cd ..
```

### Шаг 4: Запуск

```batch
# Прямой запуск
.\build\ascii_rtx_viewer.exe

# Или через скрипт
.\run.bat
```

---

## 🎮 Использование

### Что выводится при запуске

```
=== ASCII RTX v1 - Ray Tracing Engine ===
Initializing...
Creating engine (1280x720)...
Starting render loop...
Press Ctrl+C to exit

Frame: 0 | FPS: inf
Frame: 30 | FPS: 73.9857
Frame: 60 | FPS: 72.9665
...
Render complete!
Total frames: 500
Total time: 7.00398 seconds
Average FPS: 71.3879
```

Приложение:
- ✓ Инициализирует движок
- ✓ Загружает сцену (сферы, куб, плоскость)
- ✓ Рендерит 500 кадров с анимацией
- ✓ Выводит статистику производительности

### Редактирование сцены

Чтобы изменить сцену, отредактируйте `src/config/default.cpp`:

```cpp
void init_default_config() {
	// ... существующий код ...

	// Добавить новую сферу
	g_config.scene.objects[4].type = 0;      // 0=sphere, 1=box, 2=plane
	g_config.scene.objects[4].px = 1.5f;     // X позиция
	g_config.scene.objects[4].py = 0.5f;     // Y позиция
	g_config.scene.objects[4].pz = 0.5f;     // Z позиция
	g_config.scene.objects[4].sx = 0.5f;     // Радиус X
	g_config.scene.objects[4].sy = 0.5f;     // Радиус Y
	g_config.scene.objects[4].sz = 0.5f;     // Радиус Z
	g_config.scene.objects[4].material_id = 4;  // Mirror material

	// Увеличить счётчик объектов
	g_config.scene.num_objects = 5;
}
```

Затем пересоберите:

```batch
cd build
cmake --build . --config Release
cd ..
.\build\ascii_rtx_viewer.exe
```

### Доступные материалы

```
material_id = 0:  Matte (матовая поверхность)
material_id = 1:  Glossy Plastic (пластик)
material_id = 2:  Mixed Material
material_id = 3:  Glass (стекло)
material_id = 4:  Mirror (зеркало)
material_id = 5:  Metal (металл)
material_id = 6:  Blue Diffuse
material_id = 7:  Emissive (светящийся)
```

### Типы геометрии

```
type = 0:  Sphere (сфера)
type = 1:  Box (куб/параллелепипед)
type = 2:  Plane (плоскость)
```

---

## 🛠️ Продвинутая конфигурация

### Параметры рендеринга

В `src/config/default.h`:

```cpp
struct RenderConfig {
	const char* chars = " .,:-~=+*#%@";  // ASCII символы (по яркости)
	int samples = 2;                     // Лучи на пиксель (2, 4, 8...)
	float exposure = 1.0f;               // Яркость (0.5-2.0)
	float gamma = 1.0f;                  // Гамма-коррекция (0.8-2.2)
	float diffuse_gi_strength = 0.5f;    // Интенсивность глобального освещения
};
```

### Параметры камеры

```cpp
struct CameraConfig {
	float radius = 2.0f;    // Расстояние от центра
	float height = 1.0f;    // Высота (Y координата)
	float fov = 45.0f;      // Поле зрения (градусы)
};
```

### Параметры окна

```cpp
struct WindowConfig {
	int width = 2560;       // Ширина в пиксельных единицах
	int height = 1440;      // Высота
	int fps = 50;           // Целевой FPS
};
```

### Параметры освещения

```cpp
struct LightConfig {
	float x = 1.0f;         // Направление X
	float y = 1.0f;         // Направление Y
	float z = 1.0f;         // Направление Z
	float intensity = 1.0f; // Интенсивность (0.5-2.0)
};
```

---

## 🐛 Диагностика и решение проблем

### Проблема: Медленный рендер

**Причина**: Слишком много сэмплов или высокое разрешение

**Решение**:
```cpp
// В default.cpp уменьшить:
g_config.render.samples = 1;  // Вместо 2-4
g_config.window.width = 640;  // Вместо 2560
g_config.window.height = 480; // Вместо 1440
```

### Проблема: "Executable not found"

**Причина**: Проект не был собран

**Решение**:
```batch
build.bat all
```

### Проблема: CMake ошибка

**Причина**: Неправильная директория сборки

**Решение**:
```powershell
Remove-Item -Recurse -Force .\build
mkdir .\build
cd .\build
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --config Release
```

### Проблема: Не найдены заголовочные файлы

**Причина**: GLM не скачан

**Решение**:
```powershell
.\download_deps.ps1
```

---

## 📊 Структура выходного файла

При запуске приложение выводит:

```
[OK] Frame: N | FPS: X.XX
```

Где:
- `N` - номер кадра (0-500)
- `X.XX` - текущая частота кадров

После завершения:
```
Total frames: 500
Total time: X.XX seconds
Average FPS: Y.YY
```

---

## 🎯 Примеры для экспериментов

### Пример 1: Добавить отражающий куб

```cpp
// В default.cpp, в init_default_config()

// Куб с зеркальной поверхностью
g_config.scene.objects[4].type = 1;           // Box
g_config.scene.objects[4].px = 0.0f;
g_config.scene.objects[4].py = 0.8f;
g_config.scene.objects[4].pz = 1.0f;
g_config.scene.objects[4].sx = 0.3f;
g_config.scene.objects[4].sy = 0.3f;
g_config.scene.objects[4].sz = 0.3f;
g_config.scene.objects[4].material_id = 4;    // Mirror
g_config.scene.num_objects = 5;
```

### Пример 2: Установить более яркое освещение

```cpp
g_config.light.intensity = 1.5f;  // Вместо 1.0f
g_config.render.exposure = 1.2f;  // Вместо 1.0f
```

### Пример 3: Повысить качество

```cpp
g_config.render.samples = 4;      // Больше лучей
g_config.window.width = 1920;     // Выше разрешение
g_config.window.height = 1080;
```

---

## 📚 Структура кода

```
src/
├── engine/          # Основной движок
├── geometry/        # Примитивы геометрии
├── config/          # Конфигурация
├── utils/           # Утилиты
├── pipeline/        # Постобработка
└── apps/viewer/     # Главное приложение
```

Каждый модуль имеет свой `.h` и `.cpp` файлы.

---

## ✨ Возможные улучшения

После базовой работы можно добавить:

- [ ] Загрузка моделей (OBJ/FBX)
- [ ] Процедурные текстуры
- [ ] Полная трассировка путей (path tracing)
- [ ] Интерактивный UI в реальном времени
- [ ] Экспорт в видео (MP4)
- [ ] CUDA ускорение (на VS 2022 Community)
- [ ] Многопоточность
- [ ] Сетевой рендеринг

---

## 📞 Контроль качества

**Система протестирована на**:
- ✅ Visual Studio 2026 Insiders
- ✅ Windows 11
- ✅ CMake 3.20+
- ✅ MSVC 19.51
- ✅ Ninja build system

**Результаты**:
- ✅ Полная компиляция без ошибок
- ✅ Успешный запуск приложения
- ✅ Стабильная производительность (~71 FPS)
- ✅ Корректные математические вычисления

---

## 📄 Дополнительная информация

- **Версия**: 1.0.0
- **Дата**: 16 апреля 2026
- **Статус**: ✅ Готово к использованию
- **Язык**: C++17
- **Платформы**: Windows, Linux, macOS

Для полной документации см. `README.md` и `BUILD.md`.

---

**Готово к использованию! 🚀**

Запустите приложение:
```batch
.\run.bat
```
