import config
from render import render_frame_buffer
from video_ascii import save_video_ascii
import pickle


def bake_frames(W, H, aspect, chars):
    total_frames = config.MODE["bake_frames"]
    duration = 1 / config.CAMERA["speed"]

    frames = []

    for i in range(total_frames):
        t = (i / total_frames) * duration

        buffer = render_frame_buffer(
            W, H, aspect,
            t,
            1/60,
            chars
        )

        frames.append(buffer)
        print(f"[BAKE] {i+1}/{total_frames}")

    return frames


def save_frames(frames):
    with open(config.MODE["save_file"], "wb") as f:
        pickle.dump(frames, f)


def load_frames():
    with open(config.MODE["save_file"], "rb") as f:
        return pickle.load(f)