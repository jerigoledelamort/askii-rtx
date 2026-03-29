import numpy as np
from numba import cuda
from engine.materials import MATERIALS


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
            [0.0, 1.5, 4.0, 8.0, 3.0, 0.2, 0.0],
        ],
        dtype=np.float32,
    )

    plane_y = np.float32(0.0)
    return spheres, boxes, plane_y

class Scene:
    def __init__(self):
        self.time = 0.0

        # CPU данные
        self.spheres = None
        self.boxes = None
        self.plane_y = None

        # GPU данные
        self.d_spheres = None
        self.d_boxes = None
        self.d_materials = None

        self.changed = True

    def update(self, dt):
        self.time += dt

        spheres, boxes, plane_y = get_scene_flat(self.time)

        # проверка изменений
        if (
            self.spheres is None
            or not np.array_equal(self.spheres, spheres)
            or not np.array_equal(self.boxes, boxes)
            or self.plane_y != plane_y
        ):
            self.changed = True

            self.spheres = spheres
            self.boxes = boxes
            self.plane_y = plane_y

            # обновляем GPU
            self.d_spheres = cuda.to_device(spheres.astype(np.float32))
            self.d_boxes = cuda.to_device(boxes.astype(np.float32))
            self.d_materials = cuda.to_device(MATERIALS.astype(np.float32))
        else:
            self.changed = False

    def get_data(self):
        return {
            "spheres": self.spheres,
            "boxes": self.boxes,
            "plane_y": self.plane_y,

            "d_spheres": self.d_spheres,
            "d_boxes": self.d_boxes,
            "d_materials": self.d_materials,

            "changed": self.changed,
        }