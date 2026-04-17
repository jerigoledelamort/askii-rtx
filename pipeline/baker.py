import math
import pickle

from config import default as config
from engine.camera import Camera
from engine.render import ascii_map


DEFAULT_SAVE_FILE = "frames.pkl"


def bake_frames(engine, W, H, aspect, chars):
    """Render offline frame sequence using the same API as realtime mode."""
    total_frames = int(config.BAKE.get("frames", 120))
    if total_frames <= 0:
        return []

    camera = Camera([0.0, 2.0, -5.0])
    frames = []
    dt = 1 / 60.0

    for i in range(total_frames):
        t = i / total_frames
        angle = t * 2.0 * math.pi

        # Небольшое орбитальное движение камеры для bake.
        camera.pos[0] = math.sin(angle) * 2.0
        camera.pos[2] = -5.0 + math.cos(angle) * 1.5

        luminance_buffer, edge_buffer, buffer_rgb, _ = engine.render(
            camera,
            dt,
            chars,
            W,
            H,
            aspect,
            1,
            1,
        )

        char_idx, edge_mask, edge_dir, diag_sign = ascii_map(
            luminance_buffer,
            edge_buffer,
            chars,
        )

        frames.append((char_idx, edge_mask, edge_dir, diag_sign, edge_buffer, buffer_rgb))
        print(f"[BAKE] {i + 1}/{total_frames}")

    return frames


def _frames_path():
    mode_cfg = getattr(config, "MODE", None)
    if isinstance(mode_cfg, dict):
        return mode_cfg.get("save_file", DEFAULT_SAVE_FILE)
    return DEFAULT_SAVE_FILE


def save_frames(frames):
    with open(_frames_path(), "wb") as f:
        pickle.dump(frames, f)


def load_frames():
    with open(_frames_path(), "rb") as f:
        return pickle.load(f)
