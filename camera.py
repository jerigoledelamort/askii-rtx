import math
import numpy as np

import config


def get_camera(angle):
    cam = config.CAMERA

    radius = cam["radius"]
    height = cam["height"]
    mode = cam.get("mode", "orbit")

    if mode == "orbit":
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        y = height
    elif mode == "wave":
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        y = height + math.sin(angle * cam["wave_speed"]) * cam["wave_amplitude"]
    else:
        x, y, z = 0.0, height, radius

    ro = np.array([x, y, z], dtype=np.float32)

    forward = np.array([-ro[0], -ro[1], -ro[2]], dtype=np.float32)
    fl = math.sqrt(forward[0] * forward[0] + forward[1] * forward[1] + forward[2] * forward[2])
    forward /= fl

    right = np.array([forward[2], 0.0, -forward[0]], dtype=np.float32)
    rl = math.sqrt(right[0] * right[0] + right[2] * right[2])
    right /= rl

    up = np.array(
        [
            right[1] * forward[2] - right[2] * forward[1],
            right[2] * forward[0] - right[0] * forward[2],
            right[0] * forward[1] - right[1] * forward[0],
        ],
        dtype=np.float32,
    )

    return ro, forward, right, up