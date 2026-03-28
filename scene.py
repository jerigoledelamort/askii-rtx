import numpy as np


def get_scene_flat(time):
    _ = time

    # (x, y, z, radius, material_id)
    spheres = np.array(
        [
            [-1.2, -0.3, -0.5, 0.3, 0.0],
            [-0.4, -0.3, -0.3, 0.3, 1.0],
            [0.0, -0.3, 0.2, 0.3, 2.0],
            [0.6, -0.3, -0.2, 0.3, 3.0],
            [1.2, -0.3, -0.4, 0.3, 4.0],
        ],
        dtype=np.float32,
    )

    # (x, y, z, sx, sy, sz, material_id)
    boxes = np.array(
        [
            [0.8, -0.1, 0.5, 0.3, 0.3, 0.3, 2.0],
            [-2.0, 0.0, 0.0, 0.1, 2.0, 2.0, 0.0],
            [2.0, 0.0, 0.0, 0.1, 2.0, 2.0, 0.0],
            [0.0, 0.0, 2.0, 2.0, 2.0, 0.1, 0.0],
        ],
        dtype=np.float32,
    )

    plane_y = np.float32(-0.6)
    return spheres, boxes, plane_y