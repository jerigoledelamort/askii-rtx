import math
import numpy as np
from numba import njit

import config
from camera import get_camera
from scene import get_scene_flat
from lighting import get_light
from tracer import trace_ray

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
    ambient_on,
    sky_on,
    soft_shadow_on,
    hard_shadow_on,
    reflection_on,
    refraction_on,
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

                color += trace_ray(
                    ro,
                    rd,
                    light,
                    bounces,
                    ambient_on,
                    sky_on,
                    soft_shadow_on,
                    hard_shadow_on,
                    reflection_on,
                    refraction_on,
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

    ambient_on = int(config.LIGHTING["ambient"])
    sky_on = int(config.LIGHTING["sky"])
    soft_shadow_on = int(config.LIGHTING["soft_shadows"])
    hard_shadow_on = int(config.LIGHTING["hard_shadows"])
    reflection_on = int(config.LIGHTING["reflections"])
    refraction_on = int(config.LIGHTING["refraction"])

    ro, forward, right, up = get_camera(camera_angle)

    # 🔥 НОВОЕ
    spheres, boxes, plane_y = get_scene_flat(scene_time)

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

                rdx = forward[0] + right[0] * nx + up[0] * ny
                rdy = forward[1] + right[1] * nx + up[1] * ny
                rdz = forward[2] + right[2] * nx + up[2] * ny

                rl = math.sqrt(rdx * rdx + rdy * rdy + rdz * rdz)
                rd = (rdx / rl, rdy / rl, rdz / rl)

                color += trace_ray(
                    ro,
                    rd,
                    light,
                    bounces,
                    ambient_on,
                    sky_on,
                    soft_shadow_on,
                    hard_shadow_on,
                    reflection_on,
                    refraction_on,
                    spheres,
                    boxes,
                    plane_y,
                )

            color /= samples
            idx = int(color * (len(chars) - 1))
            buffer[y, x] = idx

    return buffer


def draw_buffer(surface, buffer, chars, char_cache, char_w, char_h):
    for y, row in enumerate(buffer):
        for x, idx in enumerate(row):
            char = chars[idx]
            surface.blit(char_cache[char], (x * char_w, y * char_h))