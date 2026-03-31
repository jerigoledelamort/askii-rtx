import numpy as np
from numba import cuda
from engine.materials import MATERIALS
import math


def compute_vertex_normals(vertices, indices):
    normals = np.zeros_like(vertices, dtype=np.float32)

    for i0, i1, i2 in indices:
        v0 = vertices[i0]
        v1 = vertices[i1]
        v2 = vertices[i2]

        e1 = v1 - v0
        e2 = v2 - v0

        n = np.cross(e2, e1)

        length = np.linalg.norm(n)
        if length > 1e-8:
            n /= length

        normals[i0] += n
        normals[i1] += n
        normals[i2] += n

    # normalize
    for i in range(len(normals)):
        l = np.linalg.norm(normals[i])
        if l > 1e-8:
            normals[i] /= l

    return normals


def transform_vertices(vertices, tx=0.0, ty=0.0, tz=0.0, ry=0.0, rx=0.0, rz=0.0):
    out = []

    cos_y = math.cos(ry)
    sin_y = math.sin(ry)

    cos_x = math.cos(rx)
    sin_x = math.sin(rx)

    cos_z = math.cos(rz)
    sin_z = math.sin(rz)

    for v in vertices:
        x, y, z = v

        # rotate Y
        x1 = x * cos_y + z * sin_y
        z1 = -x * sin_y + z * cos_y
        y1 = y

        # rotate Z
        x2 = x1 * cos_z - y1 * sin_z
        y2 = x1 * sin_z + y1 * cos_z
        z2 = z1

        # rotate X
        y3 = y2 * cos_x - z2 * sin_x
        z3 = y2 * sin_x + z2 * cos_x
        x3 = x2

        # translate
        x3 += tx
        y3 += ty
        z3 += tz

        out.append([x3, y3, z3])

    return np.array(out, dtype=np.float32)


def create_cube_mesh(size=1.0):
    s = size * 0.5

    vertices = np.array([
        [-s, -s, -s],
        [ s, -s, -s],
        [ s,  s, -s],
        [-s,  s, -s],
        [-s, -s,  s],
        [ s, -s,  s],
        [ s,  s,  s],
        [-s,  s,  s],
    ], dtype=np.float32)

    indices = [
        (0,1,2),(0,2,3),
        (4,6,5),(4,7,6),
        (0,5,1),(0,4,5),
        (2,6,7),(2,7,3),
        (1,5,6),(1,6,2),
        (0,3,7),(0,7,4),
    ]

    return vertices, indices


def mesh_to_triangles(vertices, indices, normals, material_id=0):
    tris = []

    for i0, i1, i2 in indices:
        v0 = vertices[i0]
        v1 = vertices[i1]
        v2 = vertices[i2]

        n0 = normals[i0]
        n1 = normals[i1]
        n2 = normals[i2]

        tris.append([
            # позиции
            v0[0], v0[1], v0[2],
            v1[0], v1[1], v1[2],
            v2[0], v2[1], v2[2],

            # нормали вершин
            n0[0], n0[1], n0[2],
            n1[0], n1[1], n1[2],
            n2[0], n2[1], n2[2],

            # материал
            material_id
        ])

    return np.array(tris, dtype=np.float32)


def get_scene_flat(time):
    _ = time            # time not used yet

    spheres = np.array(
    [
        [0.0, 0.0, -2.0, 0.5, 4.0],  # сильно вниз
    ],
    dtype=np.float32,
    )

    v, i = create_cube_mesh(size=1.0)
    v = transform_vertices(
        v,
        ty=0.5,     # поднять над полом
        ry=0.5,     # поворот
        rx=0.5,      # наклон
        rz=0.5
    )
    normals = compute_vertex_normals(v, i)
    triangles = mesh_to_triangles(v, i, normals, material_id=0)

    # (x, y, z, sx, sy, sz, material_id)
    boxes = np.zeros((0, 7), dtype=np.float32)

    plane_y = np.float32(0.0)

    return spheres, boxes, triangles, plane_y

class Scene:
    def __init__(self):
        self.time = 0.0
        
        # CPU данные
        self.spheres = None
        self.boxes = None
        self.plane_y = None
        self.triangles = None

        # GPU данные
        self.d_spheres = None
        self.d_boxes = None
        self.d_materials = None
        self.d_triangles = None

        self.changed = True

    def update(self, dt):
        self.time += dt

        spheres, boxes, triangles, plane_y = get_scene_flat(self.time)

        # проверка изменений
        if (
            self.spheres is None
            or not np.array_equal(self.spheres, spheres)
            or not np.array_equal(self.boxes, boxes)
            or not np.array_equal(self.triangles, triangles)
            or self.plane_y != plane_y
        ):
            self.changed = True

            self.spheres = spheres
            self.boxes = boxes
            self.plane_y = plane_y
            self.triangles = triangles

            # обновляем GPU
            self.d_spheres = cuda.to_device(spheres.astype(np.float32))
            self.d_boxes = cuda.to_device(boxes.astype(np.float32))
            self.d_materials = cuda.to_device(MATERIALS.astype(np.float32))
            self.d_triangles = cuda.to_device(triangles.astype(np.float32))
        else:
            self.changed = False

    def get_data(self):
        return {
            "spheres": self.spheres,
            "boxes": self.boxes,
            "plane_y": self.plane_y,
            "triangles": self.triangles,

            "d_spheres": self.d_spheres,
            "d_boxes": self.d_boxes,
            "d_materials": self.d_materials,
            "d_triangles": self.d_triangles,

            "changed": self.changed,
        }