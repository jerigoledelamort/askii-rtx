# ASCII RTX — GPU ASCII Path Tracer (Python + CUDA)

Полноценный интерактивный ASCII-рендерер на Python с трассировкой лучей/путей на GPU (Numba CUDA), постобработкой и экспортом анимации в `.mp4`.

Проект сочетает:
- **реалтайм-превью** с управлением в UI;
- **offline bake** кадров с повышенным качеством;
- **конвертацию в цветной ASCII** с адаптивным выбором символов;
- **материалы с отражением/преломлением/Fresnel** и стохастическим GI.

---

## Содержание
- [1. Возможности](#1-возможности)
- [2. Технологический стек и зависимости](#2-технологический-стек-и-зависимости)
- [3. Требования к окружению](#3-требования-к-окружению)
- [4. Быстрый старт](#4-быстрый-старт)
- [5. Режимы работы](#5-режимы-работы)
- [6. Архитектура проекта](#6-архитектура-проекта)
- [7. Пайплайн рендера (пошагово)](#7-пайплайн-рендера-пошагово)
- [8. Конфигурация (`config.py`)](#8-конфигурация-configpy)
- [9. UI и управление](#9-ui-и-управление)
- [10. Сцена и материалы](#10-сцена-и-материалы)
- [11. Bake и экспорт видео](#11-bake-и-экспорт-видео)
- [12. Производительность и качество](#12-производительность-и-качество)
- [13. Ограничения и известные нюансы](#13-ограничения-и-известные-нюансы)
- [14. Отладка и troubleshooting](#14-отладка-и-troubleshooting)
- [15. Как расширять проект](#15-как-расширять-проект)

---

## 1. Возможности

- GPU path tracing на **Numba CUDA kernels**.
- Поддержка геометрии:
  - sphere;
  - axis-aligned box (AABB);
  - infinite plane.
- Материалы:
  - diffuse/specular;
  - reflectivity + roughness;
  - refractivity + IOR + absorption;
  - Fresnel (Schlick).
- Освещение:
  - ambient;
  - sky contribution;
  - hard/soft shadows.
- Постпроцесс:
  - ACES tonemapping;
  - gamma;
  - fog по depth;
  - edge enhancement (depth/normal discontinuities);
  - dithering;
  - адаптивное соответствие luminance → ASCII symbol (через histogram/CDF).
- Накопление сэмплов между кадрами и reset accumulation при изменении камеры/сцены.
- UI на `pygame` для live-настроек.
- Экспорт:
  - `.pkl` (кадры)
  - `.mp4` (ASCII-видео через `imageio` + `libx264`).

---

## 2. Технологический стек и зависимости

### Runtime-библиотеки

- **Python 3.10+** (рекомендуется).
- **numpy** — математика, буферы, histogram/CDF, массивы сцены.
- **numba** — JIT и CUDA kernels (`numba.cuda`, `@cuda.jit`, RNG states).
- **pygame** — окно, input, UI, отрисовка символов и surface.
- **imageio** — запись видео `.mp4`.
- **imageio-ffmpeg** (рекомендуется) — backend для `libx264`.

### Стандартная библиотека

`math`, `sys`, `os`, `pickle`, `datetime`.

### Установка зависимостей

```bash
pip install numpy numba pygame imageio imageio-ffmpeg
```

> Если используете conda:
>
> ```bash
> conda install numpy numba pygame imageio
> ```
>
> и при необходимости отдельно ffmpeg/imageio-ffmpeg.

---

## 3. Требования к окружению

Так как рендер — CUDA-ориентированный, нужен:

1. **NVIDIA GPU** с поддержкой CUDA.
2. Установленный **NVIDIA driver**.
3. Совместимые версии `numba` + CUDA runtime/driver.
4. Для видео-экспорта — доступный ffmpeg codec `libx264`.

### Проверка, что CUDA видна Numba

```bash
python -c "from numba import cuda; print(cuda.is_available())"
```

Если `False`, realtime/bake через `render.py` не запустятся корректно.

---

## 4. Быстрый старт

### 4.1 Клонирование и запуск

```bash
git clone <repo-url>
cd askii-rtx
python main.py
```

### 4.2 Что происходит при старте

- Инициализируется fullscreen окно `pygame`.
- Строится ранжирование символов по яркости (`build_char_ramp`).
- Поднимается UI панель справа.
- Запускается realtime рендер (если `MODE.type = "realtime"`).

---

## 5. Режимы работы

Режим задаётся в `config.py -> MODE["type"]`:

### `"realtime"`

- Рендер в live-цикле.
- Камера/свет/флаги меняются из UI.
- Можно нажать **BAKE** в UI для офлайн просчёта и экспорта.

### `"bake"`

- На старте сразу просчитывает `BAKE.frames` кадров.
- Сохраняет `frames.pkl` и `renders/render_*.mp4`.
- После завершения переключается в `"playback"`.

### `"playback"`

- Проигрывает подготовленные кадры из памяти по кругу.

---

## 6. Архитектура проекта

```text
askii-rtx/
├── main.py                # entrypoint, loop, UI, mode orchestration
├── config.py              # все runtime/bake/render/camera/light/scenesettings
├── render.py              # CUDA path tracing kernels + postprocess + ascii mapping
├── scene.py               # плоское представление сцены (spheres, boxes, plane)
├── camera.py              # вычисление камеры + коллизии с геометрией
├── materials.py           # таблица материалов (PBR-like параметры)
├── lighting.py            # CPU/Numba lighting helpers
├── baker.py               # офлайн просчёт кадров + сохранение pkl
├── video_ascii.py         # сборка mp4 из ASCII кадров
├── char_calibration.py    # сортировка символов по яркости
├── ui.py                  # Slider / Button / Checkbox / Dropdown
├── tracer.py              # CPU/Numba tracer (legacy/альтернативный путь)
└── geometry/
    ├── sphere.py          # sphere hit
    ├── box.py             # box hit
    └── plane.py           # plane hit
```

### Архитектурные слои

1. **Presentation/UI layer**: `main.py`, `ui.py`.
2. **Render core (GPU)**: `render.py`.
3. **Scene/Camera domain**: `scene.py`, `camera.py`, `materials.py`, `lighting.py`.
4. **Offline pipeline**: `baker.py`, `video_ascii.py`.
5. **Utilities/legacy**: `char_calibration.py`, `tracer.py`, `geometry/*`.

---

## 7. Пайплайн рендера (пошагово)

Основная функция: `render_frame_buffer(W, H, aspect, scene_time, camera_angle, dt, chars)`.

### Шаг 1. Сбор параметров

Из `config.py` читаются:
- samples/bounces;
- lighting флаги;
- exposure/gamma/diffuse_gi_strength.

### Шаг 2. Подготовка камеры/сцены

- `get_camera(camera_angle)` возвращает `ro, forward, right, up`.
- `get_scene_flat(scene_time)` даёт numpy-массивы spheres/boxes + plane_y.

### Шаг 3. Проверка изменений

- Если изменилась сцена/камера/размер буфера, accumulation reset.
- Иначе продолжает копить сэмплы по кадрам.

### Шаг 4. CUDA kernel: `render_sample_kernel`

На пиксель:
- генерируется первичный луч (+ jitter для AA);
- выполняется bounce-loop (`for bounce in range(bounces)`);
- на каждом попадании:
  - intersection (`trace_scene`);
  - normal;
  - direct light + shadows;
  - выбор следующего события (reflection/refraction/diffuse) через вероятностный branching;
  - обновление throughput;
  - Russian roulette для поздних bounce.

Записываются:
- sample RGB,
- sample depth,
- sample normal,
- число реально использованных sub-samples.

### Шаг 5. CUDA kernel: `accumulate_kernel`

Обновляет глобальные accumulation buffers:
- `accum_rgb += sample_rgb * weight`
- `sample_count += weight`

### Шаг 6. CUDA kernel: `postprocess_kernel`

- деление на sample_count;
- exposure + ACES + gamma;
- saturation tweak;
- fog по depth;
- edge detection (depth/normal);
- dithering;
- формирование:
  - `buffer_rgb` (цвет символа),
  - `luminance_buffer` (для выбора ASCII символа),
  - `edge_buffer` (для усиления контуров символами).

### Шаг 7. CPU-side ASCII mapping

- histogram/CDF remap luminance;
- вычисление индекса символа в `chars`;
- edge-aware корректировка индекса.

Результат: `(idx, buffer_rgb)`.

### Шаг 8. Draw

`draw_buffer(...)` рендерит символы через кэш глифов и цветной `font.render(...)`.

---

## 8. Конфигурация (`config.py`)

Ниже все ключевые разделы и влияние на систему.

### 8.1 `WINDOW`
- `width`, `height` — сейчас практически не используются напрямую (окно fullscreen).
- `fps` — ограничение цикла UI/рендера.

### 8.2 `MODE`
- `type`: `"realtime" | "bake"`.
- `bake_frames` — legacy-поле, фактическая длина bake берётся из `BAKE["frames"]`.
- `playback_fps` — fps итогового mp4.
- `save_file` — путь к pickle (`frames.pkl`).

### 8.3 `BAKE`
- `frames` — количество кадров в офлайн рендере.
- `bounces` — bounce depth при bake (подменяет realtime `RENDER.bounces` на время bake).
- `samples` — samples per pixel для bake.
- `font_size` — параметр присутствует в UI/конфиге, но в текущем коде не подключён к реальной смене размера шрифта в runtime.

### 8.4 `RENDER`
- `chars` — исходная строка символов ASCII ramp.
- `bounces`, `samples` — realtime качество.
- `exposure`, `gamma` — тон/яркость.
- `diffuse_gi_strength` — вклад диффузного глобального освещения.

### 8.5 `FONT`
- `name`, `size` — шрифт ASCII-глифов.

### 8.6 `CAMERA`
- `mode` — есть в конфиге (`orbit|wave`), но в текущей реализации `camera.py` не использует этот флаг напрямую.
- `radius`, `height`, `speed` — активно применяются.
- `wave_*` — на будущее/legacy.

### 8.7 `LIGHT`
- `direction` — направление источника.
- `intensity` — в текущем рендер-пути не используется напрямую в `render.py` (свет нормализуется в `get_light()`).

### 8.8 `LIGHTING`
Тумблеры в UI:
- `ambient`
- `sky`
- `soft_shadows`
- `hard_shadows`
- `reflections`
- `refraction` (есть в конфиге, без отдельного чекбокса в текущем UI)
- `fresnel`

### 8.9 `SCENE`
Есть детальная декларативная структура для sphere/box/plane анимации.

**Важно:** в текущем runtime `scene.py` возвращает фиксированные `spheres/boxes/plane_y` и не читает `SCENE`. Это задел под будущую параметрическую сцену.

---

## 9. UI и управление

UI размещается справа (`UI_WIDTH = 320`) и содержит:

### Слайдеры
- `cam radius`
- `cam height`
- `cam speed`
- `frames` (bake)
- `bounces` (bake)
- `samples` (bake)
- `font size` (на данный момент без runtime-эффекта)

### Dropdown
- `render resolution` из списка preset:
  - 640×360
  - 800×450
  - 1280×720
  - 1920×1080
  - 2560×1440

### Чекбоксы
- Ambient, Sky, Soft Shadows, Hard Shadows, Reflections, Fresnel.

### Кнопки
- **BAKE** — запускает offline-проход и экспорт.
- **EXIT** — выход из приложения.

### Горячие клавиши
- `Esc` — выход.
- `F11` — toggle fullscreen.

---

## 10. Сцена и материалы

## 10.1 Геометрия

`scene.py` сейчас задаёт:
- 5 сфер;
- 4 бокса (включая стенки/объекты);
- плоскость `plane_y = 0.0`.

## 10.2 Камера

`camera.py`:
- вычисляет bounds сцены;
- двигает камеру по оси X в зависимости от угла;
- держит `z` позади центра сцены;
- выполняет collision check с sphere/AABB и корректирует `x` при пересечениях;
- возвращает ортонормальный базис `forward/right/up`.

## 10.3 Материалы

`materials.py` хранит таблицу, где на материал:

`[diffuse, specular, shininess, reflectivity, roughness, refractivity, ior, absorption, r, g, b]`

В текущем наборе есть типы:
- matte;
- glossy plastic;
- mixed;
- glass;
- mirror.

---

## 11. Bake и экспорт видео

### 11.1 Bake (`baker.py`)

- Длительность цикла: `duration = 1 / CAMERA.speed`.
- Для каждого кадра:
  - вычисляется `scene_time`;
  - вычисляется `camera_angle`;
  - рендерится ASCII-буфер;
  - сохраняется в список.

### 11.2 Сохранение кадров

`save_frames(frames)` сериализует кадры в `MODE.save_file` (`pickle`).

### 11.3 Экспорт MP4 (`video_ascii.py`)

- Создаётся `renders/`.
- Имя файла: `render_YYYY-mm-dd_HH-MM-SS.mp4`.
- Кадры рисуются через тот же `draw_buffer`, затем пишутся в `imageio` writer (`libx264`, `yuv420p`).

---

## 12. Производительность и качество

Ключевые регуляторы качества/скорости:

1. `RENDER.samples` / `BAKE.samples` — больше сэмплов = меньше шум, медленнее.
2. `RENDER.bounces` / `BAKE.bounces` — глубина путей, влияет на реализм и стоимость.
3. Разрешение рендера (dropdown) — квадратично влияет на нагрузку.
4. Флаги `soft_shadows`, `refraction`, `fresnel` — усложняют шейдинг.
5. `diffuse_gi_strength` — влияет на "заполнение" освещения.

Практический совет:
- realtime: держать `samples=1..2`, `bounces=1..2`;
- bake: повышать `samples` и `bounces` постепенно, тестируя на короткой анимации.

---

## 13. Ограничения и известные нюансы

1. Проект ориентирован на CUDA GPU; CPU fallback для основного потока рендера не подключён.
2. `tracer.py` и `geometry/*` содержат CPU/Numba-трассировщик, но main-цикл использует `render.py` (CUDA).
3. Некоторые поля `config.py` пока не участвуют в runtime логике (`SCENE`, часть camera/light параметров).
4. Поле `BAKE.font_size` сейчас не меняет фактический `pygame.font` во время работы.
5. UI-рендер и символный draw идут на CPU (`pygame`), что может стать bottleneck на высоких разрешениях.

---

## 14. Отладка и troubleshooting

### Проблема: `cuda.is_available() == False`

Проверьте:
- NVIDIA driver установлен и видит GPU (`nvidia-smi`);
- версии `numba` и CUDA runtime совместимы;
- запуск происходит в среде с доступом к GPU.

### Проблема: не сохраняется MP4 / ошибки codec

Проверьте:
- установлен ffmpeg;
- доступен `libx264`;
- установлен `imageio-ffmpeg`.

### Проблема: низкий FPS

Уменьшите:
- разрешение рендера;
- `samples`;
- `bounces`;
- отключите `soft_shadows` и/или `refraction`.

---

## 15. Как расширять проект

### 15.1 Добавить новый материал

1. Добавьте строку в `MATERIALS` (`materials.py`).
2. Назначьте `material_id` объекту в `scene.py`.
3. При необходимости расширьте логику BRDF/BTDF в `render_sample_kernel`.

### 15.2 Добавить новый примитив

1. Реализуйте `hit_*` в `render.py` (CUDA device function).
2. Интегрируйте в `trace_scene` и `get_normal`.
3. Расширьте формат scene buffer в `scene.py`.

### 15.3 Подключить декларативную `SCENE` из `config.py`

1. Напишите преобразование `config.SCENE -> numpy buffers`.
2. Поддержите `position/scale` анимации по `scene_time`.
3. Замените hardcoded массивы в `get_scene_flat`.

### 15.4 Реализовать честный camera modes (`orbit`, `wave`)

1. Использовать `CAMERA.mode`.
2. Для `wave` добавить вертикальную модуляцию `y` на основе `wave_amplitude/wave_speed`.
3. Оставить collision-safe корректировку позиции.

---

## Минимальный чеклист запуска

1. Установить зависимости.
2. Проверить `cuda.is_available()`.
3. Запустить `python main.py`.
4. Настроить realtime через UI.
5. Нажать `BAKE` для офлайн рендера и MP4.

---

Если хотите, можно следующим шагом добавить:
- `requirements.txt`/`pyproject.toml`;
- автодетект "нет CUDA" + fallback в `tracer.py`;
- полноценную загрузку сцены из `config.SCENE`;
- headless CLI для batch-рендера без UI.