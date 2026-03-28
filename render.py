import math
import numpy as np
from numba import njit

import config
from camera import get_camera
from scene import get_scene_flat
from lighting import get_light, shade

USE_NUMBA = True


@njit
def _render_frame_buffer_numba(
    W,
    H,
    aspect,
    scene_time,
    dt,
    samples,
    bounces,
    chars_len,
    light,
    ro,
    forward,
    right,
    up,
    sphere_x,
    sphere_y,
    sphere_z,
    sphere_r,
    box_x,
    box_y,
    box_z,
    box_sx,
    box_sy,
    box_sz,
    plane_h,
):
    buffer = np.zeros((H, W), dtype=np.int32)

    for x in range(W):
        for y in range(H):
            color = 0.0

            for i in range(samples):
                jx = np.random.rand()
                jy = np.random.rand()

                nx = (x + jx) / W * 2.0 - 1.0
                ny = (y + jy) / H * 2.0 - 1.0
                nx *= aspect

                t_offset = scene_time - dt * (i / samples)
                _ = t_offset  # scene is evaluated once per frame in current pipeline

                rdx = forward[0] + right[0] * nx + up[0] * ny
                rdy = forward[1] + right[1] * nx + up[1] * ny
                rdz = forward[2] + right[2] * nx + up[2] * ny

                rl = math.sqrt(rdx * rdx + rdy * rdy + rdz * rdz)
                rd = (rdx / rl, rdy / rl, rdz / rl)

                color += shade(
                    ro,
                    rd,
                    light,
                    bounces,
                    sphere_x,
                    sphere_y,
                    sphere_z,
                    sphere_r,
                    box_x,
                    box_y,
                    box_z,
                    box_sx,
                    box_sy,
                    box_sz,
                    plane_h,
                )

            color /= samples

            idx = int(color * (chars_len - 1))
            buffer[y, x] = idx

    return buffer


def _render_frame_buffer_python(
    W,
    H,
    aspect,
    scene_time,
    dt,
    samples,
    bounces,
    chars_len,
    light,
    ro,
    forward,
    right,
    up,
    sphere_x,
    sphere_y,
    sphere_z,
    sphere_r,
    box_x,
    box_y,
    box_z,
    box_sx,
    box_sy,
    box_sz,
    plane_h,
):
    buffer = np.zeros((H, W), dtype=np.int32)

    for x in range(W):
        for y in range(H):
            color = 0.0

            for i in range(samples):
                jx = np.random.rand()
                jy = np.random.rand()

                nx = (x + jx) / W * 2.0 - 1.0
                ny = (y + jy) / H * 2.0 - 1.0
                nx *= aspect

                _ = scene_time - dt * (i / samples)

                rdx = forward[0] + right[0] * nx + up[0] * ny
                rdy = forward[1] + right[1] * nx + up[1] * ny
                rdz = forward[2] + right[2] * nx + up[2] * ny

                rl = math.sqrt(rdx * rdx + rdy * rdy + rdz * rdz)
                rd = (rdx / rl, rdy / rl, rdz / rl)

                color += shade(
                    ro,
                    rd,
                    light,
                    bounces,
                    sphere_x,
                    sphere_y,
                    sphere_z,
                    sphere_r,
                    box_x,
                    box_y,
                    box_z,
                    box_sx,
                    box_sy,
                    box_sz,
                    plane_h,
                )

            color /= samples
            idx = int(color * (chars_len - 1))
            buffer[y, x] = idx

    return buffer


def render_frame_buffer(W, H, aspect, scene_time, camera_angle, dt, chars):
    light = get_light()
    samples = config.RENDER["samples"]
    bounces = config.RENDER["bounces"]

    ro, forward, right, up = get_camera(camera_angle)
    scene = get_scene_flat(scene_time)

    renderer = _render_frame_buffer_numba if USE_NUMBA else _render_frame_buffer_python
    return renderer(
        W,
        H,
        aspect,
        scene_time,
        dt,
        samples,
        bounces,
        len(chars),
        light,
        ro,
        forward,
        right,
        up,
        scene[0],
        scene[1],
        scene[2],
        scene[3],
        scene[4],
        scene[5],
        scene[6],
        scene[7],
        scene[8],
        scene[9],
        scene[10],
    )


def draw_buffer(surface, buffer, chars, char_cache, char_w, char_h):
    for y, row in enumerate(buffer):
        for x, idx in enumerate(row):
            char = chars[idx]
            surface.blit(char_cache[char], (x * char_w, y * char_h))