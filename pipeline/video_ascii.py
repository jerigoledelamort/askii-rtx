from datetime import datetime
import os

import imageio
import pygame

from config import default as config
from engine.render import draw_buffer


DEFAULT_PLAYBACK_FPS = 24


def _playback_fps():
    mode_cfg = getattr(config, "MODE", None)
    if isinstance(mode_cfg, dict):
        return int(mode_cfg.get("playback_fps", DEFAULT_PLAYBACK_FPS))
    return DEFAULT_PLAYBACK_FPS


def save_video_ascii(frames, chars, char_cache, char_w, char_h):
    if not frames:
        raise ValueError("Cannot save video: empty frame list")

    first_char_idx = frames[0][0]
    h, w = first_char_idx.shape

    width = w * char_w
    height = h * char_h

    surface = pygame.Surface((width, height))

    output_dir = "renders"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = os.path.join(output_dir, f"render_{timestamp}.mp4")

    writer = imageio.get_writer(
        filepath,
        fps=_playback_fps(),
        codec="libx264",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )

    for char_idx, edge_mask, edge_dir, diag_sign, edge_buffer, frame_rgb in frames:
        surface.fill((0, 0, 0))

        draw_buffer(
            surface,
            char_idx,
            edge_mask,
            edge_dir,
            diag_sign,
            edge_buffer,
            chars,
            char_cache,
            char_w,
            char_h,
            frame_rgb,
        )

        img = pygame.surfarray.array3d(surface)
        img = img.transpose([1, 0, 2])

        writer.append_data(img)

    writer.close()

    print(f"[VIDEO ASCII] saved to {filepath}")
