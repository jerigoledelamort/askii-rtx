import math
import config

def get_camera(time):
    cfg = config.CAMERA

    radius = cfg["radius"]
    height = cfg["height"]
    speed = cfg["speed"]

    duration = 1 / speed
    phase = time / duration
    angle = phase * 2 * math.pi

    mode = cfg.get("mode", "orbit")

    if mode == "orbit":
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        y = height

    elif mode == "wave":
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        y = height + math.sin(angle * cfg["wave_speed"]) * cfg["wave_amplitude"]

    else:
        x, y, z = 0, height, radius

    ro = (x, y, z)

    target = (0, 0, 0)

    forward = (
        target[0] - ro[0],
        target[1] - ro[1],
        target[2] - ro[2]
    )

    fl = math.sqrt(sum(i*i for i in forward))
    forward = tuple(i / fl for i in forward)

    right = (forward[2], 0, -forward[0])
    rl = math.sqrt(right[0]**2 + right[2]**2)
    right = (right[0]/rl, 0, right[2]/rl)

    up = (
        right[1]*forward[2] - right[2]*forward[1],
        right[2]*forward[0] - right[0]*forward[2],
        right[0]*forward[1] - right[1]*forward[0]
    )

    return ro, forward, right, up