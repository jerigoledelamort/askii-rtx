import numpy as np
import math
import config


def normalize(v):
    norm = np.linalg.norm(v)
    if norm < 1e-6:
        return v
    return v / norm


def cross(a, b):
    return np.cross(a, b)


def clamp(value, min_v, max_v):
    return max(min_v, min(max_v, value))


def get_camera(angle):
    radius = config.CAMERA["radius"]
    height = config.CAMERA["height"]

    # 🎯 центр сцены (ВАЖНО — внутри комнаты)
    target = np.array([0.0, 0.5, 1.5], dtype=np.float32)

    # 🔒 ограничение радиуса (чтобы не вылетать за стены)
    radius = min(radius, 1.8)

    # 🎥 orbit
    ro = np.array([
        radius * math.sin(angle),
        height,
        target[2] - radius * math.cos(angle)   # ← ВАЖНО: МИНУС
    ], dtype=np.float32)

    # 🔭 направление
    forward = normalize(target - ro)

    world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    right = normalize(cross(forward, world_up))
    up = normalize(cross(right, forward))

    return ro, forward, right, up