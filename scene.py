import math
import config


def _resolve_axis(axis):
    if axis == "x":
        return 0
    if axis == "y":
        return 1
    if axis == "z":
        return 2
    return -1


def _resolve_motion_type(motion_type):
    if motion_type == "oscillate":
        return 1
    if motion_type == "orbit":
        return 2
    return 0


def _resolve_scale_type(scale_type):
    if scale_type == "pulse":
        return 1
    return 0


def _compute_object(base_pos, base_scale, position_cfg, scale_cfg, angle, is_box):
    x, y, z = base_pos
    sx, sy, sz = base_scale

    motion_type = _resolve_motion_type(position_cfg["type"])
    if motion_type == 1:
        offset = math.sin(angle * position_cfg["speed"]) * position_cfg["amplitude"]
        axis = _resolve_axis(position_cfg["axis"])
        if axis == 0:
            x += offset
        elif axis == 1:
            y += offset
        elif axis == 2:
            z += offset
    elif motion_type == 2:
        a = angle * position_cfg["speed"]
        r = position_cfg["radius"]
        x = math.cos(a) * r
        z = math.sin(a) * r

    scale_type = _resolve_scale_type(scale_cfg["type"])
    if scale_type == 1:
        s = math.sin(angle * scale_cfg["speed"]) * scale_cfg["amplitude"]
        if is_box:
            sx += s
            sy -= s
        else:
            sx += s

    return x, y, z, sx, sy, sz


def get_scene_flat(time):
    angle = time * 2.0 * math.pi
    scene_cfg = config.SCENE

    s_cfg = scene_cfg["sphere"]
    sx, sy, sz, sr, _, _ = _compute_object(
        s_cfg["base"]["pos"],
        (s_cfg["base"]["radius"], 0.0, 0.0),
        s_cfg["position"],
        s_cfg["scale"],
        angle,
        False,
    )

    b_cfg = scene_cfg["box"]
    bx, by, bz, bsx, bsy, bsz = _compute_object(
        b_cfg["base"]["pos"],
        b_cfg["base"]["size"],
        b_cfg["position"],
        b_cfg["scale"],
        angle,
        True,
    )

    plane_h = scene_cfg["plane"]["height"]

    return sx, sy, sz, sr, bx, by, bz, bsx, bsy, bsz, plane_h


def get_scene(time):
    sx, sy, sz, sr, bx, by, bz, bsx, bsy, bsz, plane_h = get_scene_flat(time)
    return {
        "sphere": {"pos": (sx, sy, sz), "radius": sr},
        "box": {"pos": (bx, by, bz), "size": (bsx, bsy, bsz)},
        "plane": {"height": plane_h},
    }