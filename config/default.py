# ===============================
# CONFIGURATION FILE
# ===============================

# -------- WINDOW --------
WINDOW = {
    "width": 2560,
    "height": 1440,
    "fps": 50
}

BAKE = {
    "frames": 120,        
}

# -------- TAA --------
TEMPORAL = {
    "enabled": 1,

    # базовое смешивание
    "base_alpha": 0.30,

    # влияние движения камеры
    "motion_scale": 10.0,
    "motion_boost": 0.5,

    # clamp
    "base_clamp": 0.02,
    "clamp_adaptive_scale": 2.0,
}

# -------- RENDER --------
RENDER = {
    "chars": " .,:-~=+*#%@",
    "samples": 2,
    "exposure": 1.0,
    "gamma": 1.0,
    "diffuse_gi_strength": 0.4,
}

# -------- FONT --------
FONT = {
    "name": "Consolas",
    "size": 8
}

PERFORMANCE = {
    "target_chars": 32000
}

# -------- CAMERA --------
CAMERA = {
    "radius": 2.0,
    "height": 1.0,
}

# -------- LIGHT --------
LIGHT = {
    "direction": (0.0, 1.0, 0.0),
}

LIGHTING = {
    "ambient": 1,
    "hard_shadows": 1,
}

# -------- SCENE --------
# ВАЖНО:
# base = исходное состояние
# position = перемещение
# scale = изменение размера

SCENE = {

    "sphere": {
        "base": {
            "pos": (1.0, 0, 0),     # начальная позиция
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
            "type": "none",      # none | pulse
            "amplitude": 0.2,     # изменение радиуса
            "speed": 2.0
        }
    },

    "box": {
        "base": {
            "pos": (-1.0, 0, 0),
            "size": (0.5, 0.5, 0.5)
        },

        "position": {
            "type": "none",
            "axis": "y",
            "amplitude": 0.2,
            "speed": 2.0
        },

        "scale": {
            "type": "none",
            "amplitude": 0.1,
            "speed": 2.0
        }
    },

    "plane": {
        "height": -0.5
    }
}