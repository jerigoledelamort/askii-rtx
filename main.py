import pygame
import sys
import config

from render import render_frame_buffer, draw_buffer
from baker import bake_frames, save_frames
from video_ascii import save_video_ascii  # ← ВАЖНО: сюда

WIDTH = config.WINDOW["width"]
HEIGHT = config.WINDOW["height"]
FPS = config.WINDOW["fps"]

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ASCII Raytracer")

clock = pygame.time.Clock()

font = pygame.font.SysFont(
    config.FONT["name"],
    config.FONT["size"]
)

char_w, char_h = font.size("A")

W = WIDTH // char_w
H = HEIGHT // char_h

aspect = (W * char_w) / (H * char_h)

surface = pygame.Surface((WIDTH, HEIGHT))

chars = config.RENDER["chars"]

char_cache = {
    c: font.render(c, True, (255, 255, 255))
    for c in chars
}

mode = config.MODE["type"]

frames = None
frame_index = 0

# -------- INIT --------

if mode == "bake":
    frames = bake_frames(W, H, aspect, chars)
    save_frames(frames)

    save_video_ascii(frames, chars)  # ← ОДИН РАЗ

    print("BAKE DONE")

    mode = "playback"

# -------- LOOP --------

time = 0
running = True

while running:
    dt = clock.tick(FPS) / 1000.0
    dt = min(dt, 0.033)

    time += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    surface.fill((0, 0, 0))

    if mode == "realtime":
        buffer = render_frame_buffer(W, H, aspect, time, dt, chars)
        draw_buffer(surface, buffer, chars, char_cache, char_w, char_h)

    elif mode == "playback":
        buffer = frames[frame_index]
        draw_buffer(surface, buffer, chars, char_cache, char_w, char_h)

        frame_index += 1
        if frame_index >= len(frames):
            frame_index = 0

    screen.blit(surface, (0, 0))
    pygame.display.flip()

pygame.quit()
sys.exit()