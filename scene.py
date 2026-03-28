import numpy as np


def get_scene_flat(time):
    _ = time

    # (x, y, z, radius, material_id)
    spheres = np.array(
        [
            [-1.8, 0.4, -1.5, 0.4, 0.0],
            [1.6, 0.5, 1.2, 0.5, 1.0],
            [-1.4, -0.3, 1.8, 0.3, 2.0],
            [1.7, 0.45, -1.3, 0.45, 3.0],
            [0.0, 0.35, 2.0, 0.35, 4.0],
        ],
        dtype=np.float32,
    )

    # (x, y, z, sx, sy, sz, material_id)
    boxes = np.array(
        [
            [0.0, 0.5, 0.0, 1.0, 1.0, 1.0, 2.0],
            [-4.0, 1.5, 0, 0.2, 3.0, 8.0, 0.0],
            [4.0, 1.5, 0, 0.2, 3.0, 8.0, 0.0],
            [0.0, 1.5, -4.0, 8.0, 3.0, 0.2, 0.0],
        ],
        dtype=np.float32,
    )

    plane_y = np.float32(0.0)
    return spheres, boxes, plane_y