import pygame
import sys
import config

from render import render_frame_buffer, draw_buffer
from baker import bake_frames, save_frames
from video_ascii import save_video_ascii
from char_calibration import build_char_ramp
from ui import Slider, Button

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

chars = build_char_ramp(config.RENDER["chars"], font)

char_w, char_h = font.size("A")

W = WIDTH // char_w
H = HEIGHT // char_h

aspect = (W * char_w) / (H * char_h)

surface = pygame.Surface((WIDTH, HEIGHT))

char_cache = {
    c: font.render(c, False, (255, 255, 255))
    for c in chars
}

mode = config.MODE["type"]

frames = None
frame_index = 0

# -------- UI --------
ui_font = pygame.font.SysFont("consolas", 16)

sliders = [
    Slider(600, 50, 200, 2, 10, config.CAMERA["radius"], "cam radius"),
    Slider(600, 100, 200, -5, 5, config.CAMERA["height"], "cam height"),
    Slider(600, 150, 200, 0.05, 1.0, config.CAMERA["speed"], "cam speed"),

    Slider(600, 250, 200, 30, 600, config.BAKE["frames"], "frames", True),
    Slider(600, 300, 200, 1, 10, config.BAKE["bounces"], "bounces", True),
    Slider(600, 350, 200, 1, 8, config.BAKE["samples"], "samples", True),
    Slider(600, 400, 200, 6, 24, config.BAKE["font_size"], "font size", True),
]

bake_button = Button(600, 460, 200, 30, "BAKE")

# -------- INIT --------

if mode == "bake":
    frames = bake_frames(W, H, aspect, chars)
    save_frames(frames)
    save_video_ascii(frames, chars, char_cache, char_w, char_h)
    print("BAKE DONE")
    mode = "playback"

# -------- LOOP --------

scene_time = 0
camera_angle = 0

running = True

while running:
    dt = clock.tick(FPS) / 1000.0
    dt = min(dt, 0.033)

    scene_time += dt  # 🔥 сцена живёт отдельно

    for event in pygame.event.get():
        bake_button.handle(event)

        if event.type == pygame.QUIT:
            running = False

        for s in sliders:
            s.handle(event)

    surface.fill((0, 0, 0))

    # --- UI → CONFIG ---
    config.CAMERA["radius"] = sliders[0].value
    config.CAMERA["height"] = sliders[1].value
    config.CAMERA["speed"] = sliders[2].value
    config.BAKE["frames"] = int(sliders[3].value)
    config.BAKE["bounces"] = int(sliders[4].value)
    config.BAKE["samples"] = int(sliders[5].value)
    config.BAKE["font_size"] = int(sliders[6].value)

    # 🔥 только камера зависит от speed
    camera_angle += config.CAMERA["speed"] * dt * 2 * 3.1415926

    if mode == "realtime":
        buffer = render_frame_buffer(W, H, aspect, scene_time, camera_angle, dt, chars)
        draw_buffer(surface, buffer, chars, char_cache, char_w, char_h)

    elif mode == "playback":
        buffer = frames[frame_index]
        draw_buffer(surface, buffer, chars, char_cache, char_w, char_h)

        frame_index += 1
        if frame_index >= len(frames):
            frame_index = 0

    screen.blit(surface, (0, 0))

    for s in sliders:
        s.draw(screen, ui_font)

    bake_button.draw(screen, ui_font)
    if bake_button.clicked:
        bake_button.clicked = False

        print("START BAKE")

        old_samples = config.RENDER["samples"]
        old_bounces = config.RENDER["bounces"]

        config.RENDER["samples"] = config.BAKE["samples"]
        config.RENDER["bounces"] = config.BAKE["bounces"]

        frames = bake_frames(W, H, aspect, chars)
        save_frames(frames)
        save_video_ascii(frames, chars, char_cache, char_w, char_h)

        print("BAKE DONE")

        config.RENDER["samples"] = old_samples
        config.RENDER["bounces"] = old_bounces
    pygame.display.flip()

pygame.quit()
sys.exit()