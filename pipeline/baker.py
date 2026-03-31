from config import default as config
import pickle
import math


def bake_frames(engine, W, H, aspect, chars):
    total_frames = config.BAKE["frames"]
    duration = 1 / config.CAMERA["speed"]

    frames = []

    for i in range(total_frames):
        t = (i / total_frames) * duration

        scene_time = t
        camera_angle = t * config.CAMERA["speed"] * 2 * math.pi
        dt = 1/60

        buffer_idx, buffer_rgb = engine.render(
            camera_angle,
            dt,
            chars,
            W,
            H,
            aspect
        )

        frames.append((buffer_idx, buffer_rgb))
        print(f"[BAKE] {i+1}/{total_frames}")

    return frames


def save_frames(frames):
    with open(config.MODE["save_file"], "wb") as f:
        pickle.dump(frames, f)


def load_frames():
    with open(config.MODE["save_file"], "rb") as f:
        return pickle.load(f)