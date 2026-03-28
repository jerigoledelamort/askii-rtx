import pygame
import sys
import config

from render import render_frame_buffer, draw_buffer
from baker import bake_frames, save_frames
from video_ascii import save_video_ascii
from char_calibration import build_char_ramp
from ui import Slider, Button, Dropdown, Checkbox

FPS = config.WINDOW["fps"]

RESOLUTIONS = [(640, 360), (800, 450), (1280, 720), (1920, 1080), (2560, 1440)]
INITIAL_RESOLUTION_INDEX = 2

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("ASCII Raytracer")
DISPLAY_WIDTH, DISPLAY_HEIGHT = screen.get_size()

clock = pygame.time.Clock()

font = pygame.font.SysFont(
    config.FONT["name"],
    config.FONT["size"]
)

chars = build_char_ramp(config.RENDER["chars"], font)
char_w, char_h = font.size("A")

char_cache = {
    c: font.render(c, False, (255, 255, 255))
    for c in chars
}

mode = config.MODE["type"]

frames = None
frame_index = 0

# -------- UI --------
ui_font = pygame.font.SysFont("consolas", 16)
PANEL_PADDING = 20
SLIDER_STEP_Y = 56
TOP_Y = 50
CHECKBOX_START_Y = TOP_Y + SLIDER_STEP_Y * 11 + 28
CHECKBOX_STEP_Y = 32

resolution_index = INITIAL_RESOLUTION_INDEX
RENDER_WIDTH, RENDER_HEIGHT = RESOLUTIONS[resolution_index]
UI_WIDTH = int(RENDER_WIDTH * 0.25)
WINDOW_WIDTH = RENDER_WIDTH + UI_WIDTH
W = RENDER_WIDTH // char_w
H = RENDER_HEIGHT // char_h
aspect = (W * char_w) / (H * char_h)

render_surface = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT))
ui_surface = pygame.Surface((UI_WIDTH, RENDER_HEIGHT))
frame_surface = pygame.Surface((WINDOW_WIDTH, RENDER_HEIGHT))


def create_ui_controls(ui_width, selected_resolution):
    slider_width = ui_width - PANEL_PADDING * 2
    sliders_local = [
        Slider(PANEL_PADDING, TOP_Y + SLIDER_STEP_Y * 0, slider_width, 2, 10, config.CAMERA["radius"], "cam radius"),
        Slider(PANEL_PADDING, TOP_Y + SLIDER_STEP_Y * 1, slider_width, -5, 5, config.CAMERA["height"], "cam height"),
        Slider(PANEL_PADDING, TOP_Y + SLIDER_STEP_Y * 2, slider_width, 0.05, 1.0, config.CAMERA["speed"], "cam speed"),
        Slider(PANEL_PADDING, TOP_Y + SLIDER_STEP_Y * 5, slider_width, 30, 600, config.BAKE["frames"], "frames", True),
        Slider(PANEL_PADDING, TOP_Y + SLIDER_STEP_Y * 6, slider_width, 1, 10, config.BAKE["bounces"], "bounces", True),
        Slider(PANEL_PADDING, TOP_Y + SLIDER_STEP_Y * 7, slider_width, 1, 8, config.BAKE["samples"], "samples", True),
        Slider(PANEL_PADDING, TOP_Y + SLIDER_STEP_Y * 8, slider_width, 6, 24, config.BAKE["font_size"], "font size", True),
    ]
    resolution_options = [f"{i}: {w}x{h}" for i, (w, h) in enumerate(RESOLUTIONS)]
    dropdown = Dropdown(
        PANEL_PADDING,
        TOP_Y + SLIDER_STEP_Y * 4,
        slider_width,
        28,
        resolution_options,
        selected_resolution,
        "render resolution"
    )
    button = Button(PANEL_PADDING, TOP_Y + SLIDER_STEP_Y * 9 + 12, slider_width, 30, "BAKE")
    exit_button = Button(PANEL_PADDING, TOP_Y + SLIDER_STEP_Y * 10 + 20, slider_width, 30, "EXIT")
    checkboxes_local = [
        Checkbox(PANEL_PADDING, CHECKBOX_START_Y + CHECKBOX_STEP_Y * 0, 20, "Ambient", int(config.LIGHTING["ambient"])),
        Checkbox(PANEL_PADDING, CHECKBOX_START_Y + CHECKBOX_STEP_Y * 1, 20, "Sky", int(config.LIGHTING["sky"])),
        Checkbox(PANEL_PADDING, CHECKBOX_START_Y + CHECKBOX_STEP_Y * 2, 20, "Soft Shadows", int(config.LIGHTING["soft_shadows"])),
        Checkbox(PANEL_PADDING, CHECKBOX_START_Y + CHECKBOX_STEP_Y * 3, 20, "Hard Shadows", int(config.LIGHTING["hard_shadows"])),
        Checkbox(PANEL_PADDING, CHECKBOX_START_Y + CHECKBOX_STEP_Y * 4, 20, "Reflections", int(config.LIGHTING["reflections"])),
        Checkbox(PANEL_PADDING, CHECKBOX_START_Y + CHECKBOX_STEP_Y * 5, 20, "Refraction", int(config.LIGHTING["refraction"])),
        Checkbox(PANEL_PADDING, CHECKBOX_START_Y + CHECKBOX_STEP_Y * 6, 20, "Fresnel", int(config.LIGHTING["fresnel"])),
    ]
    return sliders_local, dropdown, button, exit_button, checkboxes_local


sliders, resolution_dropdown, bake_button, exit_button, checkboxes = create_ui_controls(UI_WIDTH, resolution_index)


def apply_resolution(index):
    global resolution_index, RENDER_WIDTH, RENDER_HEIGHT, UI_WIDTH, WINDOW_WIDTH
    global W, H, aspect, render_surface, ui_surface, frame_surface
    global sliders, resolution_dropdown, bake_button, exit_button, checkboxes

    resolution_index = index
    RENDER_WIDTH, RENDER_HEIGHT = RESOLUTIONS[resolution_index]
    UI_WIDTH = int(RENDER_WIDTH * 0.25)
    WINDOW_WIDTH = RENDER_WIDTH + UI_WIDTH
    W = RENDER_WIDTH // char_w
    H = RENDER_HEIGHT // char_h
    aspect = (W * char_w) / (H * char_h)

    render_surface = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT))
    ui_surface = pygame.Surface((UI_WIDTH, RENDER_HEIGHT))
    frame_surface = pygame.Surface((WINDOW_WIDTH, RENDER_HEIGHT))
    sliders, resolution_dropdown, bake_button, exit_button, checkboxes = create_ui_controls(UI_WIDTH, resolution_index)


def get_scaled_layout():
    scale = min(DISPLAY_WIDTH / WINDOW_WIDTH, DISPLAY_HEIGHT / RENDER_HEIGHT)
    scaled_w = int(WINDOW_WIDTH * scale)
    scaled_h = int(RENDER_HEIGHT * scale)
    offset_x = (DISPLAY_WIDTH - scaled_w) // 2
    offset_y = (DISPLAY_HEIGHT - scaled_h) // 2
    return scale, scaled_w, scaled_h, offset_x, offset_y


def display_to_logical(pos):
    scale, scaled_w, scaled_h, offset_x, offset_y = get_scaled_layout()
    px, py = pos
    if px < offset_x or py < offset_y or px >= offset_x + scaled_w or py >= offset_y + scaled_h:
        return None
    local_x = int((px - offset_x) / scale)
    local_y = int((py - offset_y) / scale)
    return local_x, local_y

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
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
                DISPLAY_WIDTH, DISPLAY_HEIGHT = screen.get_size()

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            logical_pos = display_to_logical(event.pos)
            if logical_pos and logical_pos[0] >= RENDER_WIDTH:
                bake_button.handle(event, x_offset=RENDER_WIDTH, mouse_pos=logical_pos)
                exit_button.handle(event, x_offset=RENDER_WIDTH, mouse_pos=logical_pos)
                for s in sliders:
                    s.handle(event, x_offset=RENDER_WIDTH, mouse_pos=logical_pos)
                resolution_dropdown.handle(event, x_offset=RENDER_WIDTH, mouse_pos=logical_pos)
                for c in checkboxes:
                    c.handle(event, x_offset=RENDER_WIDTH, mouse_pos=logical_pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            logical_pos = display_to_logical(event.pos)
            if logical_pos:
                bake_button.handle(event, x_offset=RENDER_WIDTH, mouse_pos=logical_pos)
                exit_button.handle(event, x_offset=RENDER_WIDTH, mouse_pos=logical_pos)
                resolution_dropdown.handle(event, x_offset=RENDER_WIDTH, mouse_pos=logical_pos)
            else:
                resolution_dropdown.expanded = False
            for s in sliders:
                s.handle(event, x_offset=RENDER_WIDTH, mouse_pos=logical_pos)

    render_surface.fill((0, 0, 0))
    ui_surface.fill((24, 24, 24))

    # --- UI → CONFIG ---
    config.CAMERA["radius"] = sliders[0].value
    config.CAMERA["height"] = sliders[1].value
    config.CAMERA["speed"] = sliders[2].value
    config.BAKE["frames"] = int(sliders[3].value)
    config.BAKE["bounces"] = int(sliders[4].value)
    config.BAKE["samples"] = int(sliders[5].value)
    config.BAKE["font_size"] = int(sliders[6].value)
    config.LIGHTING["ambient"] = int(checkboxes[0].value)
    config.LIGHTING["sky"] = int(checkboxes[1].value)
    config.LIGHTING["soft_shadows"] = int(checkboxes[2].value)
    config.LIGHTING["hard_shadows"] = int(checkboxes[3].value)
    config.LIGHTING["reflections"] = int(checkboxes[4].value)
    config.LIGHTING["refraction"] = int(checkboxes[5].value)
    config.LIGHTING["fresnel"] = int(checkboxes[6].value)

    if resolution_dropdown.changed:
        resolution_dropdown.changed = False
        apply_resolution(resolution_dropdown.selected_index)

    # 🔥 только камера зависит от speed
    camera_angle += config.CAMERA["speed"] * dt * 2 * 3.1415926

    if mode == "realtime":
        buffer = render_frame_buffer(W, H, aspect, scene_time, camera_angle, dt, chars)
        draw_buffer(render_surface, buffer, chars, char_cache, char_w, char_h)

    elif mode == "playback":
        buffer = frames[frame_index]
        draw_buffer(render_surface, buffer, chars, char_cache, char_w, char_h)

        frame_index += 1
        if frame_index >= len(frames):
            frame_index = 0

    for s in sliders:
        s.draw(ui_surface, ui_font)
    resolution_dropdown.draw(ui_surface, ui_font)
    for c in checkboxes:
        c.draw(ui_surface, ui_font)

    bake_button.draw(ui_surface, ui_font)
    exit_button.draw(ui_surface, ui_font)
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

    if exit_button.clicked:
        exit_button.clicked = False
        running = False

    frame_surface.blit(render_surface, (0, 0))
    frame_surface.blit(ui_surface, (RENDER_WIDTH, 0))
    scale, scaled_w, scaled_h, offset_x, offset_y = get_scaled_layout()
    scaled = pygame.transform.scale(frame_surface, (scaled_w, scaled_h))
    screen.fill((0, 0, 0))
    screen.blit(scaled, (offset_x, offset_y))
    pygame.display.flip()

pygame.quit()
sys.exit()