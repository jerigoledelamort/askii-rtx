import math

import numpy as np

from engine.scene import get_scene_flat


def normalize(v):
    norm = np.linalg.norm(v)
    if norm < 1e-6:
        return v
    return v / norm


def cross(a, b):
    return np.cross(a, b)


def clamp(value, min_v, max_v):
    return max(min_v, min(max_v, value))


def compute_scene_bounds(spheres, boxes):
    min_x = np.inf
    max_x = -np.inf
    min_z = np.inf
    max_z = -np.inf

    for s in spheres:
        x, _, z, r, _ = s
        min_x = min(min_x, x - r)
        max_x = max(max_x, x + r)
        min_z = min(min_z, z - r)
        max_z = max(max_z, z + r)

    for b in boxes:
        x, _, z, sx, _, sz, _ = b
        min_x = min(min_x, x - sx)
        max_x = max(max_x, x + sx)
        min_z = min(min_z, z - sz)
        max_z = max(max_z, z + sz)

    if not np.isfinite(min_x):
        min_x = max_x = min_z = max_z = 0.0

    return float(min_x), float(max_x), float(min_z), float(max_z)


def check_collision_camera(cam_pos, spheres, boxes, margin=0.3):
    cx, cy, cz = cam_pos

    for s in spheres:
        sx, sy, sz, sr, _ = s
        dx = cx - sx
        dy = cy - sy
        dz = cz - sz
        if dx * dx + dy * dy + dz * dz < (sr + margin) * (sr + margin):
            return True

    for b in boxes:
        bx, by, bz, bsx, bsy, bsz, _ = b
        min_bx = bx - (bsx + margin)
        max_bx = bx + (bsx + margin)
        min_by = by - (bsy + margin)
        max_by = by + (bsy + margin)
        min_bz = bz - (bsz + margin)
        max_bz = bz + (bsz + margin)

        if (
            min_bx <= cx <= max_bx
            and min_by <= cy <= max_by
            and min_bz <= cz <= max_bz
        ):
            return True

    return False


def _resolve_camera_x_collision(desired_x, cy, cz, spheres, boxes, margin=0.3):
    x = float(desired_x)

    for _ in range(2):
        adjusted = False

        for s in spheres:
            sx, sy, sz, sr, _ = s
            dy = cy - sy
            dz = cz - sz
            rr = sr + margin
            radial_sq = rr * rr - dy * dy - dz * dz
            if radial_sq <= 0.0:
                continue

            half_span_x = math.sqrt(radial_sq)
            left = sx - half_span_x
            right = sx + half_span_x

            if left <= x <= right:
                x = left if x <= sx else right
                adjusted = True

        for b in boxes:
            bx, by, bz, bsx, bsy, bsz, _ = b
            min_by = by - (bsy + margin)
            max_by = by + (bsy + margin)
            min_bz = bz - (bsz + margin)
            max_bz = bz + (bsz + margin)

            if not (min_by <= cy <= max_by and min_bz <= cz <= max_bz):
                continue

            min_bx = bx - (bsx + margin)
            max_bx = bx + (bsx + margin)
            if min_bx <= x <= max_bx:
                x = min_bx if x <= bx else max_bx
                adjusted = True

        if not adjusted:
            break

    return x


class Camera:
    def __init__(self, pos):
        self.pos = np.array(pos, dtype=np.float32)

        self.yaw = 0.0
        self.pitch = 0.0

        self.speed = 5.0
        self.sensitivity = 0.002

        # FOV
        self.fov = 1.0
        self.fov_min = 0.3
        self.fov_max = 2.5

    def get_vectors(self):
        forward = np.array([
            math.cos(self.pitch) * math.sin(self.yaw),
            math.sin(self.pitch),
            math.cos(self.pitch) * math.cos(self.yaw),
        ], dtype=np.float32)

        forward = normalize(forward)

        world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        right = normalize(cross(forward, world_up))
        up = normalize(cross(right, forward))

        # применяем FOV
        right *= self.fov
        up *= self.fov

        return forward, right, up