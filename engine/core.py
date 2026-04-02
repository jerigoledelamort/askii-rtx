from engine.camera import Camera
from engine.render import render_frame_buffer, reset_accumulation_buffers
from engine.render import RendererState
from engine.scene import Scene
from engine.render import ascii_map
import numpy as np


class Engine:
    def __init__(self, config):
        self.scene = Scene()
        self.config = config
        self.render_settings = config.RENDER
        self.light_data = config.LIGHT
        self.lighting_settings = config.LIGHTING
        self.camera_settings = config.CAMERA

        self.state = RendererState()

    def render(self, camera, dt, chars, W, H, aspect, char_w, char_h):
        # 1. сцена
        self.scene.update(dt)
        scene_data = self.scene.get_data()

        # 2. камера
        ro = camera.pos
        forward, right, up = camera.get_vectors()

        camera_data = {
            "ro": ro,
            "forward": forward,
            "right": right,
            "up": up
        }

        # 3. рендер
        # --- GPU ---
        luminance, edge, rgb = render_frame_buffer(
            W, H, aspect,
            scene_data,
            camera_data,
            self.render_settings,
            self.config.TEMPORAL,   
            self.lighting_settings,
            self.light_data,
            chars,
            self.state
        )

        buffer_idx = ascii_map(luminance, edge, chars)

        return buffer_idx, rgb

    def reset(self):
        self.state = RendererState()