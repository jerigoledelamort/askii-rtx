import pygame
import imageio
import os
from datetime import datetime
import config

from render import draw_buffer


def save_video_ascii(frames, chars, char_cache, char_w, char_h):
    # --- размеры ---
    first_idx = frames[0][0]
    h = len(first_idx)
    w = len(first_idx[0])

    width = w * char_w
    height = h * char_h

    surface = pygame.Surface((width, height))

    # --- папка ---
    output_dir = "renders"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = os.path.join(output_dir, f"render_{timestamp}.mp4")

    writer = imageio.get_writer(
        filepath,
        fps=config.MODE["playback_fps"],
        codec="libx264",
        ffmpeg_params=["-pix_fmt", "yuv420p"]
    )

    for frame_idx, frame_rgb in frames:
        surface.fill((0, 0, 0))

        # 🔥 ВАЖНО: используем ТОТ ЖЕ рендер
        draw_buffer(surface, frame_idx, chars, char_cache, char_w, char_h, frame_rgb)

        # --- surface → numpy ---
        img = pygame.surfarray.array3d(surface)
        img = img.transpose([1, 0, 2])

        writer.append_data(img)

    writer.close()

    print(f"[VIDEO ASCII] saved to {filepath}")