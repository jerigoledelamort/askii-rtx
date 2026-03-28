import math
import config
import numpy as np


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

    spheres = np.array([
        [-1.2, -0.3, -0.5, 0.3, 0],
        [-0.4, -0.3, -0.3, 0.3, 1],
        [ 0.0, -0.3,  0.2, 0.3, 2],
        [ 0.6, -0.3, -0.2, 0.3, 3],
        [ 1.2, -0.3, -0.4, 0.3, 4],
    ], dtype=np.float32)

    boxes = np.array([
        # куб
        [0.8, -0.1, 0.5, 0.3, 0.3, 0.3, 2],

        # стены
        [-2.0, 0.0, 0.0, 0.1, 2.0, 2.0, 0],
        [ 2.0, 0.0, 0.0, 0.1, 2.0, 2.0, 0],
        [ 0.0, 0.0, 2.0, 2.0, 2.0, 0.1, 0],
    ], dtype=np.float32)

    plane_y = -0.6

    return spheres, boxes, plane_y


def get_scene_flat(time):
    # --- СФЕРЫ ---
    # (x, y, z, radius, material_id)
    spheres = [
        (-1.2, -0.3, -0.5, 0.3, 0),  # матовый
        (-0.4, -0.3, -0.3, 0.3, 1),  # глянцевый
        (0.0, -0.3, 0.2, 0.3, 2),    # смешанный
        (0.6, -0.3, -0.2, 0.3, 3),   # стекло
        (1.2, -0.3, -0.4, 0.3, 4),   # зеркало
    ]

    # --- БОКСЫ ---
    # (x, y, z, sx, sy, sz, material_id)
    boxes = [
        # куб
        (0.8, -0.1, 0.5, 0.3, 0.3, 0.3, 2),

        # стены (ВАЖНО — это просто боксы)
        (-2.0, 0.0, 0.0, 0.1, 2.0, 2.0, 0),  # левая
        (2.0, 0.0, 0.0, 0.1, 2.0, 2.0, 0),   # правая
        (0.0, 0.0, 2.0, 2.0, 2.0, 0.1, 0),   # задняя
    ]

    # пол
    plane_y = -0.6

    return spheres, boxes, plane_y