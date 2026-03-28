import math
import numpy as np
from numba import njit

from geometry.sphere import hit_sphere
from geometry.box import hit_box
from geometry.plane import hit_plane
from lighting import local_lighting, reflect
from materials import MATERIALS


@njit
def trace_scene(ro, rd, spheres, boxes, plane_h):
    t_min = -1.0
    mat = -1
    hit_type = -1
    hit_index = -1

    # --- spheres ---
    for i in range(spheres.shape[0]):
        sx = spheres[i, 0]
        sy = spheres[i, 1]
        sz = spheres[i, 2]
        sr = spheres[i, 3]
        sm = int(spheres[i, 4])

        t = hit_sphere(ro, rd, sx, sy, sz, sr)
        if t > 0.0 and (t_min < 0.0 or t < t_min):
            t_min = t
            mat = sm
            hit_type = 1
            hit_index = i

    # --- boxes ---
    for i in range(boxes.shape[0]):
        bx = boxes[i, 0]
        by = boxes[i, 1]
        bz = boxes[i, 2]
        bsx = boxes[i, 3]
        bsy = boxes[i, 4]
        bsz = boxes[i, 5]
        bm = int(boxes[i, 6])

        t = hit_box(ro, rd, bx, by, bz, bsx, bsy, bsz)
        if t > 0.0 and (t_min < 0.0 or t < t_min):
            t_min = t
            mat = bm
            hit_type = 2
            hit_index = i

    # --- plane ---
    t = hit_plane(ro, rd, plane_h)
    if t > 0.0 and (t_min < 0.0 or t < t_min):
        t_min = t
        mat = 0
        hit_type = 0
        hit_index = -1

    return t_min, mat, hit_type, hit_index


@njit
def get_normal(hit_x, hit_y, hit_z, hit_type, hit_index, spheres, boxes):

    if hit_type == 0:
        return 0.0, 1.0, 0.0

    if hit_type == 1:
        sx = spheres[hit_index, 0]
        sy = spheres[hit_index, 1]
        sz = spheres[hit_index, 2]

        nx = hit_x - sx
        ny = hit_y - sy
        nz = hit_z - sz

    else:
        bx = boxes[hit_index, 0]
        by = boxes[hit_index, 1]
        bz = boxes[hit_index, 2]

        dx = hit_x - bx
        dy = hit_y - by
        dz = hit_z - bz

        abs_dx = abs(dx)
        abs_dy = abs(dy)
        abs_dz = abs(dz)

        if abs_dx > abs_dy and abs_dx > abs_dz:
            nx = 1.0 if dx > 0 else -1.0
            ny = 0.0
            nz = 0.0
        elif abs_dy > abs_dz:
            nx = 0.0
            ny = 1.0 if dy > 0 else -1.0
            nz = 0.0
        else:
            nx = 0.0
            ny = 0.0
            nz = 1.0 if dz > 0 else -1.0

    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length > 0.0:
        inv = 1.0 / length
        return nx*inv, ny*inv, nz*inv

    return 0.0, 1.0, 0.0


@njit
def random_unit_vector():
    z = np.random.rand() * 2.0 - 1.0
    a = np.random.rand() * 2.0 * math.pi
    r = math.sqrt(max(0.0, 1.0 - z * z))
    return r * math.cos(a), r * math.sin(a), z


@njit
def compute_shadow(
    hit_x, hit_y, hit_z,
    nx, ny, nz,
    light,
    soft_shadow_on,
    hard_shadow_on,
    spheres,
    boxes,
    plane_h
):
    eps = 1e-3
    shadow_ro = (hit_x + nx * eps, hit_y + ny * eps, hit_z + nz * eps)

    # --- SOFT SHADOW ---
    if soft_shadow_on == 1:
        visible = 0.0
        samples = 4

        for _ in range(samples):
            jitter_x = light[0] + ((np.random.rand() - 0.5) * 0.1)
            jitter_y = light[1] + ((np.random.rand() - 0.5) * 0.1)
            jitter_z = light[2] + ((np.random.rand() - 0.5) * 0.1)

            jl = math.sqrt(jitter_x*jitter_x + jitter_y*jitter_y + jitter_z*jitter_z)
            jitter_light = (jitter_x / jl, jitter_y / jl, jitter_z / jl)

            t_shadow, _ = trace_scene(
                shadow_ro,
                jitter_light,
                spheres,
                boxes,
                plane_h,
            )

            if t_shadow < 0.0:
                visible += 1.0

        return visible / samples

    # --- HARD SHADOW ---
    if hard_shadow_on == 1:
        t_shadow, _ = trace_scene(
            shadow_ro,
            light,
            spheres,
            boxes,
            plane_h,
        )

        return 0.0 if t_shadow > 0.0 else 1.0

    return 1.0


@njit
def trace_ray(
    ro, rd, light, bounces,
    ambient_on, sky_on, soft_shadow_on, hard_shadow_on,
    reflection_on, refraction_on,
    spheres, boxes, plane_h
):
    t, mat_id, hit_type, hit_index = trace_scene(ro, rd, spheres, boxes, plane_h)

    if t < 0.0:
        if sky_on == 1:
            return 0.2 + 0.5 * (rd[1] * 0.5 + 0.5)
        return 0.0

    hit_x = ro[0] + rd[0] * t
    hit_y = ro[1] + rd[1] * t
    hit_z = ro[2] + rd[2] * t

    nx, ny, nz = get_normal(
        hit_x, hit_y, hit_z,
        hit_type,
        hit_index,
        spheres,
        boxes
    )
    normal = (nx, ny, nz)

    lambert = nx * light[0] + ny * light[1] + nz * light[2]
    if lambert < 0.0:
        lambert = 0.0

    shadow = compute_shadow(
        hit_x, hit_y, hit_z,
        nx, ny, nz,
        light,
        soft_shadow_on,
        hard_shadow_on,
        spheres,
        boxes,
        plane_h
    )

    local_color = local_lighting(rd, normal, light, mat_id, lambert, shadow, ambient_on)
    color = local_color

    reflectivity = MATERIALS[mat_id, 3]
    roughness = MATERIALS[mat_id, 4]

    if reflection_on == 1 and bounces > 0 and reflectivity > 0.0:
        rx, ry, rz = reflect(rd, normal)

        reflected = trace_ray(
            (hit_x + nx * 1e-3, hit_y + ny * 1e-3, hit_z + nz * 1e-3),
            (rx, ry, rz),
            light,
            bounces - 1,
            ambient_on, sky_on, soft_shadow_on, hard_shadow_on,
            reflection_on, refraction_on,
            spheres, boxes, plane_h
        )

        color = (1.0 - reflectivity) * local_color + reflectivity * reflected

    return color