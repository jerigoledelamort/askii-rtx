# ===============================
# CONFIGURATION FILE
# ===============================

# -------- WINDOW --------
WINDOW = {
    "width": 1080,
    "height": 720,
    "fps": 50
}

# -------- MODE --------
MODE = {
    "type": "realtime",            # "realtime" | "bake"
    "bake_frames": 120,        # количество кадров цикла
    "playback_fps": 30,
    "save_file": "frames.pkl"
}

BAKE = {
    "frames": 120,        # длина анимации
    "bounces": 4,         # отражения
    "samples": 1,         # антиалиасинг
    "font_size": 12       # финальный размер
}

# -------- RENDER --------
RENDER = {
    "chars": " .'`^\",:;Il!i~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "bounces": 1,
    "samples": 1
}

# -------- FONT --------
FONT = {
    "name": "Consolas",
    "size": 12
}

# -------- CAMERA --------
CAMERA = {
    "mode": "orbit",           # orbit | wave

    "radius": 2.0,             # дистанция до центра
    "height": 1.0,             # базовая высота

    "speed": 0.2,              # оборотов в секунду (задаёт длительность цикла)

    "wave_amplitude": 0.3,     # вертикальное движение
    "wave_speed": 2.0
}

# -------- LIGHT --------
LIGHT = {
    "direction": (0.5, 0.5, -1.0),
    "intensity": 1.0
}

# -------- SCENE --------
# ВАЖНО:
# base = исходное состояние
# position = перемещение
# scale = изменение размера

SCENE = {

    "sphere": {
        "base": {
            "pos": (0.5, 0, 0),     # начальная позиция
            "radius": 0.5         # базовый радиус
        },

        "position": {
            "type": "none",      # none | oscillate | orbit

            "axis": "x",          # для oscillate
            "amplitude": 0.0,     # смещение (0 = отключено)
            "speed": 1.0,

            "radius": 0.7         # для orbit
        },

        "scale": {
            "type": "pulse",      # none | pulse
            "amplitude": 0.2,     # изменение радиуса
            "speed": 2.0
        }
    },

    "box": {
        "base": {
            "pos": (-0.5, 0, 0),
            "size": (0.4, 0.4, 0.4)
        },

        "position": {
            "type": "oscillate",
            "axis": "y",
            "amplitude": 0.2,
            "speed": 2.0
        },

        "scale": {
            "type": "pulse",
            "amplitude": 0.1,
            "speed": 2.0
        }
    },

    "plane": {
        "height": -0.5
    }
}