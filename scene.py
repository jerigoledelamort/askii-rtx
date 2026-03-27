import math
import config


def get_scene(time):
    duration = 1 / config.CAMERA["speed"]
    phase = time / duration
    angle = phase * 2 * math.pi

    scene_cfg = config.SCENE

    # =========================
    # SPHERE
    # =========================

    s_cfg = scene_cfg["sphere"]

    pos = list(s_cfg["base"]["pos"])
    radius = s_cfg["base"]["radius"]

    # --- POSITION ---
    motion = s_cfg["position"]

    if motion["type"] == "oscillate":
        offset = math.sin(angle * motion["speed"]) * motion["amplitude"]

        axis = motion["axis"]
        if axis == "x":
            pos[0] += offset
        elif axis == "y":
            pos[1] += offset
        elif axis == "z":
            pos[2] += offset

    elif motion["type"] == "orbit":
        a = angle * motion["speed"]
        r = motion["radius"]

        pos[0] = math.cos(a) * r
        pos[2] = math.sin(a) * r

    # --- SCALE ---
    scale = s_cfg["scale"]

    if scale["type"] == "pulse":
        radius += math.sin(angle * scale["speed"]) * scale["amplitude"]

    sphere = {
        "pos": tuple(pos),
        "radius": radius
    }

    # =========================
    # BOX
    # =========================

    b_cfg = scene_cfg["box"]

    pos = list(b_cfg["base"]["pos"])
    size = list(b_cfg["base"]["size"])

    # --- POSITION ---
    motion = b_cfg["position"]

    if motion["type"] == "oscillate":
        offset = math.sin(angle * motion["speed"]) * motion["amplitude"]

        axis = motion["axis"]
        if axis == "x":
            pos[0] += offset
        elif axis == "y":
            pos[1] += offset
        elif axis == "z":
            pos[2] += offset

    elif motion["type"] == "orbit":
        a = angle * motion["speed"]
        r = motion["radius"]

        pos[0] = math.cos(a) * r
        pos[2] = math.sin(a) * r

    # --- SCALE (неравномерный, чтобы было видно деформацию) ---
    scale = b_cfg["scale"]

    if scale["type"] == "pulse":
        s = math.sin(angle * scale["speed"]) * scale["amplitude"]

        size[0] += s
        size[1] -= s

    box = {
        "pos": tuple(pos),
        "size": tuple(size)
    }

    # =========================

    return {
        "sphere": sphere,
        "box": box,
        "plane": scene_cfg["plane"]
    }