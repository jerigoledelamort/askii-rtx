import math
import numpy as np
from numba import njit

import config
from materials import MATERIALS
from tracer import trace


def get_light():
    light = config.LIGHT["direction"]
    l = math.sqrt(light[0] * light[0] + light[1] * light[1] + light[2] * light[2])
    return (light[0] / l, light[1] / l, light[2] / l)


@njit
def get_normal(
    hit_x, hit_y, hit_z, mat_id,
    sphere_x, sphere_y, sphere_z,
    box_x, box_y, box_z,
    box_sx, box_sy, box_sz
):
    if mat_id == 1:
        nx = hit_x - sphere_x
        ny = hit_y - sphere_y
        nz = hit_z - sphere_z

    elif mat_id == 2:
        min_x = box_x - box_sx
        max_x = box_x + box_sx
        min_y = box_y - box_sy
        max_y = box_y + box_sy
        min_z = box_z - box_sz
        max_z = box_z + box_sz

        dx_min = abs(hit_x - min_x)
        dx_max = abs(max_x - hit_x)
        dy_min = abs(hit_y - min_y)
        dy_max = abs(max_y - hit_y)
        dz_min = abs(hit_z - min_z)
        dz_max = abs(max_z - hit_z)

        m = dx_min
        nx, ny, nz = -1.0, 0.0, 0.0

        if dx_max < m:
            m = dx_max
            nx, ny, nz = 1.0, 0.0, 0.0
        if dy_min < m:
            m = dy_min
            nx, ny, nz = 0.0, -1.0, 0.0
        if dy_max < m:
            m = dy_max
            nx, ny, nz = 0.0, 1.0, 0.0
        if dz_min < m:
            m = dz_min
            nx, ny, nz = 0.0, 0.0, -1.0
        if dz_max < m:
            nx, ny, nz = 0.0, 0.0, 1.0

    else:
        nx, ny, nz = 0.0, 1.0, 0.0

    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length > 0.0:
        inv = 1.0 / length
        nx *= inv
        ny *= inv
        nz *= inv

    return nx, ny, nz


@njit
def reflect(rd, normal):
    dot = rd[0]*normal[0] + rd[1]*normal[1] + rd[2]*normal[2]
    rx = rd[0] - 2.0 * dot * normal[0]
    ry = rd[1] - 2.0 * dot * normal[1]
    rz = rd[2] - 2.0 * dot * normal[2]
    return rx, ry, rz


@njit
def shade(
    ro, rd, light, bounces,
    sphere_x, sphere_y, sphere_z, sphere_r,
    box_x, box_y, box_z, box_sx, box_sy, box_sz,
    plane_h,
):
    t, mat_id = trace(
        ro, rd,
        sphere_x, sphere_y, sphere_z, sphere_r,
        box_x, box_y, box_z, box_sx, box_sy, box_sz,
        plane_h,
    )

    if t < 0.0:
        return 0.0

    hit_x = ro[0] + rd[0] * t
    hit_y = ro[1] + rd[1] * t
    hit_z = ro[2] + rd[2] * t

    nx, ny, nz = get_normal(
        hit_x, hit_y, hit_z, mat_id,
        sphere_x, sphere_y, sphere_z,
        box_x, box_y, box_z,
        box_sx, box_sy, box_sz,
    )

    lambert = nx * light[0] + ny * light[1] + nz * light[2]
    if lambert < 0.0:
        lambert = 0.0

    diffuse = MATERIALS[mat_id, 0]
    specular = MATERIALS[mat_id, 1]
    roughness = MATERIALS[mat_id, 2]

    eps = 1e-3
    shadow_ro = (
        hit_x + nx * eps,
        hit_y + ny * eps,
        hit_z + nz * eps,
    )

    t_shadow, _ = trace(
        shadow_ro, light,
        sphere_x, sphere_y, sphere_z, sphere_r,
        box_x, box_y, box_z, box_sx, box_sy, box_sz,
        plane_h,
    )

    shadow = 0.0 if t_shadow > 0.0 else 1.0

    color = diffuse * lambert * shadow

    if bounces > 0:
        rx, ry, rz = reflect(rd, (nx, ny, nz))

        rx += roughness * ((np.random.rand() * 2.0) - 1.0) * 0.05
        ry += roughness * ((np.random.rand() * 2.0) - 1.0) * 0.05
        rz += roughness * ((np.random.rand() * 2.0) - 1.0) * 0.05

        r_len = math.sqrt(rx * rx + ry * ry + rz * rz)
        if r_len > 0.0:
            inv = 1.0 / r_len
            rx *= inv
            ry *= inv
            rz *= inv

        reflect_dir = (rx, ry, rz)

        reflect_ro = (
            hit_x + nx * eps,
            hit_y + ny * eps,
            hit_z + nz * eps,
        )

        reflected = shade(
            reflect_ro, reflect_dir, light, bounces - 1,
            sphere_x, sphere_y, sphere_z, sphere_r,
            box_x, box_y, box_z, box_sx, box_sy, box_sz,
            plane_h,
        )

        color = color * (1.0 - specular) + reflected * specular

    if color < 0.0:
        return 0.0
    if color > 1.0:
        return 1.0

    return color