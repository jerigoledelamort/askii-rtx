import pygame
import sys
import config
import math

from render import render_frame_buffer, draw_buffer
from baker import bake_frames, save_frames
from video_ascii import save_video_ascii
from char_calibration import build_char_ramp
from ui import Slider, Button, Dropdown, Checkbox

FPS = config.WINDOW["fps"]

RESOLUTIONS = [(640, 360), (800, 450), (1280, 720), (1920, 1080), (2560, 1440)]
INITIAL_RESOLUTION_INDEX = 2
UI_WIDTH = 320
UI_FONT_SIZE = 16
UI_PADDING_TOP = 20
UI_SPACING = 40
PANEL_PADDING = 20
SCROLL_SPEED = 30
FOOTER_HEIGHT = 120

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("ASCII Raytracer")
DISPLAY_WIDTH, DISPLAY_HEIGHT = screen.get_size()
UI_HEIGHT = DISPLAY_HEIGHT

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

ui_font = pygame.font.SysFont("consolas", UI_FONT_SIZE)

resolution_index = INITIAL_RESOLUTION_INDEX
RENDER_WIDTH, RENDER_HEIGHT = RESOLUTIONS[resolution_index]
W = RENDER_WIDTH // char_w
H = RENDER_HEIGHT // char_h
aspect = (W * char_w) / (H * char_h)

scroll_offset = 0

render_surface = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT))
ui_surface = pygame.Surface((UI_WIDTH, UI_HEIGHT))


def create_ui_controls(ui_width, selected_resolution):
    slider_width = ui_width - PANEL_PADDING * 2

    y = UI_PADDING_TOP
    sliders_local = [
        Slider(PANEL_PADDING, y + UI_SPACING * 0, slider_width, 2, 10, config.CAMERA["radius"], "cam radius"),
        Slider(PANEL_PADDING, y + UI_SPACING * 1, slider_width, -5, 5, config.CAMERA["height"], "cam height"),
        Slider(PANEL_PADDING, y + UI_SPACING * 2, slider_width, 0.05, 1.0, config.CAMERA["speed"], "cam speed"),
        Slider(PANEL_PADDING, y + UI_SPACING * 3, slider_width, 30, 600, config.BAKE["frames"], "frames", True),
        Slider(PANEL_PADDING, y + UI_SPACING * 4, slider_width, 1, 10, config.BAKE["bounces"], "bounces", True),
        Slider(PANEL_PADDING, y + UI_SPACING * 5, slider_width, 1, 8, config.BAKE["samples"], "samples", True),
        Slider(PANEL_PADDING, y + UI_SPACING * 6, slider_width, 6, 24, config.BAKE["font_size"], "font size", True),
    ]

    resolution_options = [f"{i}: {w}x{h}" for i, (w, h) in enumerate(RESOLUTIONS)]
    dropdown = Dropdown(
        PANEL_PADDING,
        y + UI_SPACING * 7,
        slider_width,
        28,
        resolution_options,
        selected_resolution,
        "render resolution",
    )

    bake_button = Button(PANEL_PADDING, 0, slider_width, 30, "BAKE")
    exit_button = Button(PANEL_PADDING, 0, slider_width, 30, "EXIT")

    checkbox_start_y = y + UI_SPACING * 8
    checkboxes_local = [
        Checkbox(PANEL_PADDING, checkbox_start_y + UI_SPACING * 0, 20, "Ambient", int(config.LIGHTING["ambient"]), key="ambient"),
        Checkbox(PANEL_PADDING, checkbox_start_y + UI_SPACING * 1, 20, "Sky", int(config.LIGHTING["sky"]), key="sky"),
        Checkbox(PANEL_PADDING, checkbox_start_y + UI_SPACING * 2, 20, "Soft Shadows", int(config.LIGHTING["soft_shadows"]), key="soft_shadows"),
        Checkbox(PANEL_PADDING, checkbox_start_y + UI_SPACING * 3, 20, "Hard Shadows", int(config.LIGHTING["hard_shadows"]), key="hard_shadows"),
        Checkbox(PANEL_PADDING, checkbox_start_y + UI_SPACING * 4, 20, "Reflections", int(config.LIGHTING["reflections"]), key="reflections"),
        Checkbox(PANEL_PADDING, checkbox_start_y + UI_SPACING * 5, 20, "Fresnel", int(config.LIGHTING["fresnel"]), key="fresnel"),
    ]

    return sliders_local, dropdown, bake_button, exit_button, checkboxes_local


def get_ui_content_height(sliders_local, dropdown_local, button_local, exit_button_local, checkboxes_local):
    bottom = 0

    for s in sliders_local:
        bottom = max(bottom, s.rect.bottom)

    bottom = max(bottom, dropdown_local.rect.bottom)

    for c in checkboxes_local:
        bottom = max(bottom, c.rect.bottom)

    return bottom + PANEL_PADDING


def clamp_scroll():
    global scroll_offset
    content_height = get_ui_content_height(sliders, resolution_dropdown, bake_button, exit_button, checkboxes)
    scroll_area_height = max(0, UI_HEIGHT - FOOTER_HEIGHT)
    max_scroll = max(0, content_height - scroll_area_height)
    scroll_offset = max(0, min(scroll_offset, max_scroll))


def layout_footer_buttons():
    bake_button.rect.y = UI_HEIGHT - 80
    exit_button.rect.y = UI_HEIGHT - 40


sliders, resolution_dropdown, bake_button, exit_button, checkboxes = create_ui_controls(UI_WIDTH, resolution_index)
layout_footer_buttons()


def apply_resolution(index):
    global resolution_index, RENDER_WIDTH, RENDER_HEIGHT
    global W, H, aspect, render_surface
    global sliders, resolution_dropdown, bake_button, exit_button, checkboxes, scroll_offset

    resolution_index = index
    RENDER_WIDTH, RENDER_HEIGHT = RESOLUTIONS[resolution_index]
    W = RENDER_WIDTH // char_w
    H = RENDER_HEIGHT // char_h
    aspect = (W * char_w) / (H * char_h)

    render_surface = pygame.Surface((RENDER_WIDTH, RENDER_HEIGHT))
    sliders, resolution_dropdown, bake_button, exit_button, checkboxes = create_ui_controls(UI_WIDTH, resolution_index)
    layout_footer_buttons()
    scroll_offset = 0
    clamp_scroll()


def get_render_layout():
    available_width = max(1, DISPLAY_WIDTH - UI_WIDTH)
    scale = min(available_width / RENDER_WIDTH, DISPLAY_HEIGHT / RENDER_HEIGHT)
    scaled_w = int(RENDER_WIDTH * scale)
    scaled_h = int(RENDER_HEIGHT * scale)
    render_x = (available_width - scaled_w) // 2
    render_y = (DISPLAY_HEIGHT - scaled_h) // 2
    return scale, scaled_w, scaled_h, render_x, render_y


def is_inside_ui(pos):
    return pos[0] >= (DISPLAY_WIDTH - UI_WIDTH)


def is_inside_ui_scroll_area(pos):
    if not is_inside_ui(pos):
        return False
    return pos[1] < (UI_HEIGHT - FOOTER_HEIGHT)


if mode == "bake":
    frames = bake_frames(W, H, aspect, chars)
    save_frames(frames)
    save_video_ascii(frames, chars, char_cache, char_w, char_h)
    print("BAKE DONE")
    mode = "playback"

scene_time = 0
camera_angle = 0
running = True

while running:
    dt = clock.tick(FPS) / 1000.0
    dt = min(dt, 0.033)
    scene_time += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
                DISPLAY_WIDTH, DISPLAY_HEIGHT = screen.get_size()
                UI_HEIGHT = DISPLAY_HEIGHT
                ui_surface = pygame.Surface((UI_WIDTH, UI_HEIGHT))
                layout_footer_buttons()
                clamp_scroll()

        if event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            if is_inside_ui_scroll_area(mouse_pos):
                scroll_offset -= event.y * SCROLL_SPEED
                clamp_scroll()

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            if hasattr(event, "pos") and is_inside_ui(event.pos):
                ui_mouse_pos = (event.pos[0] - (DISPLAY_WIDTH - UI_WIDTH), event.pos[1])
                if ui_mouse_pos[1] >= (UI_HEIGHT - FOOTER_HEIGHT):
                    bake_button.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=0)
                    exit_button.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=0)

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        resolution_dropdown.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=scroll_offset)
                else:
                    for s in sliders:
                        s.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=scroll_offset)
                    resolution_dropdown.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=scroll_offset)
                    for c in checkboxes:
                        c.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=scroll_offset)
        elif event.type == pygame.MOUSEBUTTONUP:
            if hasattr(event, "pos") and is_inside_ui(event.pos):
                ui_mouse_pos = (event.pos[0] - (DISPLAY_WIDTH - UI_WIDTH), event.pos[1])
                bake_button.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=0)
                exit_button.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=0)
                resolution_dropdown.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=scroll_offset)
            else:
                resolution_dropdown.expanded = False
            for s in sliders:
                if hasattr(event, "pos") and is_inside_ui(event.pos):
                    ui_mouse_pos = (event.pos[0] - (DISPLAY_WIDTH - UI_WIDTH), event.pos[1])
                else:
                    ui_mouse_pos = None
                s.handle(event, mouse_pos=ui_mouse_pos, scroll_offset=scroll_offset)

    render_surface.fill((0, 0, 0))
    ui_surface.fill((24, 24, 24))

    config.CAMERA["radius"] = sliders[0].value
    config.CAMERA["height"] = sliders[1].value
    config.CAMERA["speed"] = sliders[2].value
    config.BAKE["frames"] = int(sliders[3].value)
    config.BAKE["bounces"] = int(sliders[4].value)
    config.BAKE["samples"] = int(sliders[5].value)
    config.BAKE["font_size"] = int(sliders[6].value)
    for c in checkboxes:
        config.LIGHTING[c.key] = int(c.value)

    if resolution_dropdown.changed:
        resolution_dropdown.changed = False
        apply_resolution(resolution_dropdown.selected_index)

    clamp_scroll()

    camera_angle = math.sin(scene_time * config.CAMERA["speed"]) * 0.5

    if mode == "realtime":
        buffer = render_frame_buffer(W, H, aspect, scene_time, camera_angle, dt, chars)
        draw_buffer(render_surface, buffer, chars, char_cache, char_w, char_h)

    elif mode == "playback":
        buffer = frames[frame_index]
        draw_buffer(render_surface, buffer, chars, char_cache, char_w, char_h)

        frame_index += 1
        if frame_index >= len(frames):
            frame_index = 0

    scroll_area_height = max(0, UI_HEIGHT - FOOTER_HEIGHT)
    clip_rect = pygame.Rect(0, 0, UI_WIDTH, scroll_area_height)
    ui_surface.set_clip(clip_rect)

    for s in sliders:
        s.draw(ui_surface, ui_font, -scroll_offset)
    resolution_dropdown.draw(ui_surface, ui_font, -scroll_offset)
    for c in checkboxes:
        c.draw(ui_surface, ui_font, -scroll_offset)

    ui_surface.set_clip(None)

    footer_rect = pygame.Rect(0, UI_HEIGHT - FOOTER_HEIGHT, UI_WIDTH, FOOTER_HEIGHT)
    pygame.draw.rect(ui_surface, (32, 32, 32), footer_rect)
    pygame.draw.line(ui_surface, (64, 64, 64), (0, UI_HEIGHT - FOOTER_HEIGHT), (UI_WIDTH, UI_HEIGHT - FOOTER_HEIGHT), 1)

    bake_button.draw(ui_surface, ui_font, 0)
    exit_button.draw(ui_surface, ui_font, 0)
    resolution_dropdown.draw_overlay(
        ui_surface,
        ui_font,
        0,
        max_bottom=UI_HEIGHT - FOOTER_HEIGHT,
    )
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

    screen.fill((0, 0, 0))
    scale, scaled_w, scaled_h, render_x, render_y = get_render_layout()
    scaled_render = pygame.transform.scale(render_surface, (scaled_w, scaled_h))
    screen.blit(scaled_render, (render_x, render_y))
    screen.blit(ui_surface, (DISPLAY_WIDTH - UI_WIDTH, 0))
    pygame.display.flip()

pygame.quit()
sys.exit()