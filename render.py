import math
import numpy as np
import pygame
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
    diffuse_gi_strength,
    exposure,
    gamma,
):
    buffer_idx = np.zeros((H, W), dtype=np.int32)
    buffer_rgb = np.zeros((H, W, 3), dtype=np.float32)

    for y in range(H):
        for x in range(W):
            r = 0.0
            g = 0.0
            b = 0.0

            for _ in range(samples):
                nx = ((x + np.random.rand()) / W) * 2.0 - 1.0
                ny = 1.0 - ((y + np.random.rand()) / H) * 2.0
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

                cr, cg, cb = trace_ray(
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
                    diffuse_gi_strength,
                    spheres,
                    boxes,
                    plane_h,
                )

                r += cr
                g += cg
                b += cb

            inv_samples = 1.0 / samples
            r *= inv_samples
            g *= inv_samples
            b *= inv_samples

            r *= exposure
            g *= exposure
            b *= exposure

            if gamma != 1.0:
                r = r ** gamma
                g = g ** gamma
                b = b ** gamma

            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            if luminance < 0.0:
                luminance = 0.0
            elif luminance > 1.0:
                luminance = 1.0

            max_c = max(r, g, b, 1e-6)
            nr = r / max_c
            ng = g / max_c
            nb = b / max_c

            if nr < 0.0:
                nr = 0.0
            elif nr > 1.0:
                nr = 1.0

            if ng < 0.0:
                ng = 0.0
            elif ng > 1.0:
                ng = 1.0

            if nb < 0.0:
                nb = 0.0
            elif nb > 1.0:
                nb = 1.0

            buffer_idx[y, x] = int(luminance * (chars_len - 1))
            buffer_rgb[y, x, 0] = nr
            buffer_rgb[y, x, 1] = ng
            buffer_rgb[y, x, 2] = nb

    return buffer_idx, buffer_rgb


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

    exposure = np.float32(config.RENDER.get("exposure", 1.0))
    gamma = np.float32(config.RENDER.get("gamma", 1.0))
    diffuse_gi_strength = np.float32(config.RENDER.get("diffuse_gi_strength", 0.4))

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
        diffuse_gi_strength,
        exposure,
        gamma,
    )


def draw_buffer(surface, buffer_idx, chars, char_cache, char_w, char_h, buffer_rgb=None):
    if buffer_rgb is None:
        for y, row in enumerate(buffer_idx):
            for x, idx in enumerate(row):
                char = chars[idx]
                surface.blit(char_cache[char], (x * char_w, y * char_h))
        return

    for y, row in enumerate(buffer_idx):
        for x, idx in enumerate(row):
            char = chars[idx]
            r = int(buffer_rgb[y, x, 0] * 255.0)
            g = int(buffer_rgb[y, x, 1] * 255.0)
            b = int(buffer_rgb[y, x, 2] * 255.0)
            glyph = char_cache.get((char, r, g, b))
            if glyph is None:
                glyph = pygame_font_render(char_cache, char, r, g, b)
                char_cache[(char, r, g, b)] = glyph
            surface.blit(glyph, (x * char_w, y * char_h))


def pygame_font_render(char_cache, char, r, g, b):
    font = char_cache["__font__"]
    return font.render(char, False, (r, g, b))