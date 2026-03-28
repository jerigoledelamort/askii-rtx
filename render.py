import math
import numpy as np
from numba import njit

import config
from camera import get_camera
from scene import get_scene_flat
from lighting import get_light
from tracer import trace_ray


@njit
def render_frame_buffer_numba(
    W,
    H,
    aspect,
    samples,
    bounces,
    ambient_on,
    sky_on,
    soft_shadow_on,
    hard_shadow_on,
    reflection_on,
    refraction_on,
    chars_len,
    lx,
    ly,
    lz,
    ro,
    forward,
    right,
    up,
    spheres,
    boxes,
    plane_h,
):
    buffer = np.zeros((H, W), dtype=np.int32)

    for y in range(H):
        for x in range(W):
            color = 0.0

            for _ in range(samples):
                nx = ((x + np.random.rand()) / W) * 2.0 - 1.0
                ny = ((y + np.random.rand()) / H) * 2.0 - 1.0
                nx *= aspect

                rd = np.empty(3, dtype=np.float32)
                rd[0] = forward[0] + right[0] * nx + up[0] * ny
                rd[1] = forward[1] + right[1] * nx + up[1] * ny
                rd[2] = forward[2] + right[2] * nx + up[2] * ny

                rl = math.sqrt(rd[0] * rd[0] + rd[1] * rd[1] + rd[2] * rd[2])
                inv = 1.0 / rl
                rd[0] *= inv
                rd[1] *= inv
                rd[2] *= inv

                color += trace_ray(
                    ro,
                    rd,
                    lx,
                    ly,
                    lz,
                    bounces,
                    ambient_on,
                    sky_on,
                    soft_shadow_on,
                    hard_shadow_on,
                    reflection_on,
                    refraction_on,
                    spheres,
                    boxes,
                    plane_h,
                )

            color /= samples
            if color < 0.0:
                color = 0.0
            elif color > 1.0:
                color = 1.0

            buffer[y, x] = int(color * (chars_len - 1))

    return buffer


def render_frame_buffer(W, H, aspect, scene_time, camera_angle, dt, chars):
    _ = dt

    light = get_light()

    samples = int(config.RENDER["samples"])
    bounces = int(config.RENDER["bounces"])

    ambient_on = int(config.LIGHTING["ambient"])
    sky_on = int(config.LIGHTING["sky"])
    soft_shadow_on = int(config.LIGHTING["soft_shadows"])
    hard_shadow_on = int(config.LIGHTING["hard_shadows"])
    reflection_on = int(config.LIGHTING["reflections"])
    refraction_on = int(config.LIGHTING["refraction"])

    ro, forward, right, up = get_camera(camera_angle)
    spheres, boxes, plane_y = get_scene_flat(scene_time)

    return render_frame_buffer_numba(
        W,
        H,
        aspect,
        samples,
        bounces,
        ambient_on,
        sky_on,
        soft_shadow_on,
        hard_shadow_on,
        reflection_on,
        refraction_on,
        len(chars),
        np.float32(light[0]),
        np.float32(light[1]),
        np.float32(light[2]),
        ro,
        forward,
        right,
        up,
        spheres,
        boxes,
        plane_y,
    )


def draw_buffer(surface, buffer, chars, char_cache, char_w, char_h):
    for y, row in enumerate(buffer):
        for x, idx in enumerate(row):
            char = chars[idx]
            surface.blit(char_cache[char], (x * char_w, y * char_h))