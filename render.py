from camera import get_camera
from lighting import get_light, shade
import math
import config


def render_frame_buffer(W, H, aspect, time, dt, chars):
    light = get_light()
    samples = config.RENDER["samples"]

    buffer = [[0 for _ in range(W)] for _ in range(H)]

    for x in range(W):
        for y in range(H):

            nx = (x + 0.5) / W * 2 - 1
            ny = (y + 0.5) / H * 2 - 1
            nx *= aspect

            color = 0.0

            for i in range(samples):
                t_offset = time - config.CAMERA["speed"] * dt * (i / samples)

                ro, forward, right, up = get_camera(t_offset)

                rd = (
                    forward[0] + right[0]*nx + up[0]*ny,
                    forward[1] + right[1]*nx + up[1]*ny,
                    forward[2] + right[2]*nx + up[2]*ny
                )

                rl = math.sqrt(rd[0]**2 + rd[1]**2 + rd[2]**2)
                rd = (rd[0]/rl, rd[1]/rl, rd[2]/rl)

                color += shade(ro, rd, light, t_offset)

            color /= samples

            idx = int(color * (len(chars) - 1))
            buffer[y][x] = idx

    return buffer


def draw_buffer(surface, buffer, chars, char_cache, char_w, char_h):
    for y, row in enumerate(buffer):
        for x, idx in enumerate(row):
            char = chars[idx]
            surface.blit(char_cache[char], (x * char_w, y * char_h))