import pygame
import imageio
import os
from datetime import datetime
import config


def save_video_ascii(frames, chars):
    pygame.font.init()

    # --- шрифт ---
    font = pygame.font.SysFont(
        config.FONT["name"],
        config.FONT["size"]
    )

    char_w, char_h = font.size("A")

    h = len(frames[0])
    w = len(frames[0][0])

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
        macro_block_size=None  # ← убирает warning
    )

    for frame in frames:
        surface.fill((0, 0, 0))

        for y in range(h):
            for x in range(w):
                idx = frame[y][x]
                char = chars[idx]

                # яркость (как в рендере)
                normalized = idx / (len(chars) - 1)

                # гамма-коррекция
                value = int((normalized ** 0.6) * 255)

                color = (value, value, value)

                text = font.render(char, False, color)
                surface.blit(text, (x * char_w, y * char_h))

        # --- pygame → numpy ---
        img = pygame.surfarray.array3d(surface)
        img = img.transpose([1, 0, 2])  # исправляем оси

        writer.append_data(img)

    writer.close()

    print(f"[VIDEO ASCII] saved to {filepath}")