# ASCII RTX — интерактивный ASCII path tracer на Python + CUDA

`askii-rtx` — это экспериментальный рендерер, который считает освещение на GPU (через `numba.cuda`), а выводит результат как цветной ASCII-кадр в `pygame`.

Проект поддерживает:
- realtime-просмотр сцены с UI-панелью;
- офлайн bake кадров;
- экспорт ASCII-видео в `.mp4`;
- материалы с отражением/преломлением/Fresnel;
- постобработку (тонмаппинг, edge boost, dither, туман).

## Содержание
- [1. Структура проекта](#1-структура-проекта)
- [2. Как запустить](#2-как-запустить)
- [3. Режимы работы](#3-режимы-работы)
- [4. Конфигурация](#4-конфигурация)
- [5. Как устроен рендер-пайплайн](#5-как-устроен-рендер-пайплайн)
- [6. Bake и экспорт видео](#6-bake-и-экспорт-видео)
- [7. UI и управление](#7-ui-и-управление)
- [8. Ограничения и замечания](#8-ограничения-и-замечания)

## 1. Структура проекта

```text
askii-rtx/
├── apps/viewer/main.py      # точка входа приложения (pygame + цикл + UI)
├── apps/viewer/ui.py        # Slider / Checkbox / Dropdown / Button
├── engine/core.py           # фасад Engine: scene -> camera -> render -> ascii
├── engine/render.py         # CUDA kernels, accumulation, postprocess, ascii map
├── engine/scene.py          # CPU/GPU-представление сцены
├── engine/camera.py         # расчёт камеры + базовая коллизия
├── engine/materials.py      # таблица материалов
├── engine/lighting.py       # lighting helper-функции
├── pipeline/baker.py        # офлайн рендер кадров + pickle
├── pipeline/video_ascii.py  # сборка mp4 из ASCII-кадров
├── config/default.py        # все runtime-настройки
└── utils/char_calibration.py# сортировка символов по яркости
```

## 2. Как запустить

### Требования

1. Python 3.10+
2. NVIDIA GPU + драйвер + рабочий CUDA runtime для `numba`
3. Установленные зависимости:

```bash
pip install numpy numba pygame imageio imageio-ffmpeg
```

### Проверка CUDA

```bash
python -c "from numba import cuda; print(cuda.is_available())"
```

Если вывод `False`, GPU-рендер из `engine/render.py` работать не будет.

### Запуск приложения

Из корня репозитория:

```bash
python -m apps.viewer.main
```

По умолчанию используется fullscreen-окно и режим `MODE["type"] = "realtime"`.

## 3. Режимы работы

Режим задаётся в `config/default.py`:

- `realtime` — интерактивный рендер и управление через UI.
- `bake` — при старте рендерит последовательность кадров, сохраняет `frames.pkl` и `.mp4`, затем переключается в `playback`.
- `playback` — воспроизводит ранее подготовленные кадры в цикле.

## 4. Конфигурация

Главные секции в `config/default.py`:

- `WINDOW` — FPS и базовые параметры окна.
- `MODE` — текущий режим, FPS playback, имя файла для pickle.
- `BAKE` — число кадров, качество bake (samples/bounces), размер шрифта для экспорта.
- `RENDER` — рендер-параметры (samples/bounces, exposure, gamma, GI strength, набор символов).
- `FONT` — шрифт для ASCII в realtime.
- `CAMERA` — радиус/высота/скорость движения.
- `LIGHT` и `LIGHTING` — направление света и флаги шейдинга (ambient, sky, shadows, reflections, fresnel и т.д.).
- `SCENE` — декларативные параметры объектов (в текущем состоянии часть сцены также задаётся напрямую в `engine/scene.py`).

## 5. Как устроен рендер-пайплайн

1. `Engine.render(...)` обновляет сцену (`Scene.update`) и получает её плоское представление (spheres/boxes/plane + device buffers).
2. `engine.camera.get_camera(...)` вычисляет позицию и базис камеры с ограничением по X и проверкой коллизий.
3. `engine.render.render_frame_buffer(...)` запускает CUDA-часть:
   - трассировка пересечений (sphere/box/plane);
   - bounce-loop с отражением/преломлением;
   - учёт материалов (`engine/materials.py`);
   - накопление сэмплов между кадрами;
   - постобработка (ACES-подобный тонмаппинг, gamma, fog, edge enhancement, dithering).
4. `ascii_map(...)` превращает luminance в индексы символов.
5. `draw_buffer(...)` рисует кадр в `pygame.Surface`.

## 6. Bake и экспорт видео

- Bake запускается либо при `MODE["type"] == "bake"`, либо кнопкой **BAKE** в UI.
- `pipeline/baker.py` формирует массив кадров и может сохранять его в `frames.pkl`.
- `pipeline/video_ascii.py` отрисовывает каждый кадр тем же `draw_buffer(...)` и пишет `renders/render_<timestamp>.mp4` через `imageio` + `libx264`.

## 7. UI и управление

В правой панели доступны:
- слайдеры камеры (`radius`, `height`, `speed`);
- bake-параметры (`frames`, `bounces`, `samples`, `font size`);
- выбор разрешения рендера (dropdown);
- чекбоксы lighting-флагов;
- кнопки **BAKE** и **EXIT**.

Горячие клавиши:
- `Esc` — выход;
- `F11` — toggle fullscreen.

## 8. Ограничения и замечания

- Проект CUDA-зависим: на машинах без совместимой NVIDIA/CUDA рендер не стартует.
- В репозитории есть legacy-модуль `tracer.py`, но основной путь сейчас — через `engine/*`.
- В каталоге есть `__pycache__` артефакты; для чистых коммитов их обычно не хранят.
- Конфиг и реализация сцены частично дублируют друг друга: `SCENE` в конфиге не полностью определяет финальную геометрию, так как `engine/scene.py` содержит жёстко заданные массивы примитивов.