import math
import numpy as np
from numba import njit

from geometry.sphere import hit_sphere
from geometry.box import hit_box
from geometry.plane import hit_plane
from lighting import local_lighting, reflect_components
from materials import MATERIALS


HIT_BIAS = 1e-3


@njit
def trace_scene(ro, rd, spheres, boxes, plane_h):
    t_min = -1.0
    mat = -1
    hit_type = -1
    hit_index = -1

    sphere_count = spheres.shape[0]
    for i in range(sphere_count):
        t = hit_sphere(ro, rd, spheres[i, 0], spheres[i, 1], spheres[i, 2], spheres[i, 3])
        if t > 0.0 and (t_min < 0.0 or t < t_min):
            t_min = t
            mat = int(spheres[i, 4])
            hit_type = 1
            hit_index = i

    box_count = boxes.shape[0]
    for i in range(box_count):
        t = hit_box(
            ro,
            rd,
            boxes[i, 0],
            boxes[i, 1],
            boxes[i, 2],
            boxes[i, 3],
            boxes[i, 4],
            boxes[i, 5],
        )
        if t > 0.0 and (t_min < 0.0 or t < t_min):
            t_min = t
            mat = int(boxes[i, 6])
            hit_type = 2
            hit_index = i

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
        nx = hit_x - spheres[hit_index, 0]
        ny = hit_y - spheres[hit_index, 1]
        nz = hit_z - spheres[hit_index, 2]
    else:
        dx = hit_x - boxes[hit_index, 0]
        dy = hit_y - boxes[hit_index, 1]
        dz = hit_z - boxes[hit_index, 2]

        abs_dx = abs(dx)
        abs_dy = abs(dy)
        abs_dz = abs(dz)

        if abs_dx > abs_dy and abs_dx > abs_dz:
            nx = 1.0 if dx > 0.0 else -1.0
            ny = 0.0
            nz = 0.0
        elif abs_dy > abs_dz:
            nx = 0.0
            ny = 1.0 if dy > 0.0 else -1.0
            nz = 0.0
        else:
            nx = 0.0
            ny = 0.0
            nz = 1.0 if dz > 0.0 else -1.0

    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length > 0.0:
        inv = 1.0 / length
        return nx * inv, ny * inv, nz * inv

    return 0.0, 1.0, 0.0


@njit
def compute_shadow(
    hit_x,
    hit_y,
    hit_z,
    nx,
    ny,
    nz,
    lx,
    ly,
    lz,
    soft_shadow_on,
    hard_shadow_on,
    spheres,
    boxes,
    plane_h,
):
    eps = 1e-3
    shadow_ro = np.empty(3, dtype=np.float32)
    shadow_ro[0] = hit_x + nx * eps
    shadow_ro[1] = hit_y + ny * eps
    shadow_ro[2] = hit_z + nz * eps

    if soft_shadow_on == 1:
        visible = 0.0
        samples = 4

        for _ in range(samples):
            jitter_rd = np.empty(3, dtype=np.float32)
            jitter_rd[0] = lx + (np.random.rand() - 0.5) * 0.1
            jitter_rd[1] = ly + (np.random.rand() - 0.5) * 0.1
            jitter_rd[2] = lz + (np.random.rand() - 0.5) * 0.1

            jl = math.sqrt(jitter_rd[0] * jitter_rd[0] + jitter_rd[1] * jitter_rd[1] + jitter_rd[2] * jitter_rd[2])
            inv = 1.0 / jl
            jitter_rd[0] *= inv
            jitter_rd[1] *= inv
            jitter_rd[2] *= inv

            t_shadow, _, _, _ = trace_scene(shadow_ro, jitter_rd, spheres, boxes, plane_h)
            if t_shadow < 0.0:
                visible += 1.0

        return visible / samples

    if hard_shadow_on == 1:
        light_rd = np.empty(3, dtype=np.float32)
        light_rd[0] = lx
        light_rd[1] = ly
        light_rd[2] = lz
        t_shadow, _, _, _ = trace_scene(shadow_ro, light_rd, spheres, boxes, plane_h)
        return 0.0 if t_shadow > 0.0 else 1.0

    return 1.0


@njit
def trace_ray(
    ro,
    rd,
    lx,
    ly,
    lz,
    bounces,
    ambient_on,
    sky_on,
    soft_shadow_on,
    hard_shadow_on,
    reflection_on,
    refraction_on,
    diffuse_gi_strength,
    spheres,
    boxes,
    plane_h,
):
    _ = refraction_on
    if bounces <= 0:
        return 0.0, 0.0, 0.0
    
    t, mat_id, hit_type, hit_index = trace_scene(ro, rd, spheres, boxes, plane_h)

    if t < 0.0:
        if sky_on == 1:
            sky = 0.2 + 0.5 * (rd[1] * 0.5 + 0.5)
            return sky, sky, sky
        return 0.0, 0.0, 0.0

    hit_x = ro[0] + rd[0] * t
    hit_y = ro[1] + rd[1] * t
    hit_z = ro[2] + rd[2] * t

    nx, ny, nz = get_normal(hit_x, hit_y, hit_z, hit_type, hit_index, spheres, boxes)

    lambert = nx * lx + ny * ly + nz * lz
    if lambert < 0.0:
        lambert = 0.0

    shadow = compute_shadow(
        hit_x,
        hit_y,
        hit_z,
        nx,
        ny,
        nz,
        lx,
        ly,
        lz,
        soft_shadow_on,
        hard_shadow_on,
        spheres,
        boxes,
        plane_h,
    )

    lighting = local_lighting(
        rd[0], rd[1], rd[2], nx, ny, nz, lx, ly, lz, mat_id, lambert, shadow, ambient_on
    )

    base_r = MATERIALS[mat_id, 6]
    base_g = MATERIALS[mat_id, 7]
    base_b = MATERIALS[mat_id, 8]

    r = base_r * lighting
    g = base_g * lighting
    b = base_b * lighting

    reflectivity = MATERIALS[mat_id, 3]
    diffuse_weight = 1.0 - reflectivity

    if diffuse_weight > 0.0 and bounces > 0:
        bounce_ro = np.empty(3, dtype=np.float32)
        bounce_ro[0] = hit_x + nx * HIT_BIAS
        bounce_ro[1] = hit_y + ny * HIT_BIAS
        bounce_ro[2] = hit_z + nz * HIT_BIAS

        bounce_rd = np.empty(3, dtype=np.float32)
        bounce_rd[0] = nx + (np.random.rand() - 0.5)
        bounce_rd[1] = ny + (np.random.rand() - 0.5)
        bounce_rd[2] = nz + (np.random.rand() - 0.5)

        dl = math.sqrt(
            bounce_rd[0] * bounce_rd[0] +
            bounce_rd[1] * bounce_rd[1] +
            bounce_rd[2] * bounce_rd[2]
        )
        if dl > 0.0:
            inv_dl = 1.0 / dl
            bounce_rd[0] *= inv_dl
            bounce_rd[1] *= inv_dl
            bounce_rd[2] *= inv_dl

        n_dot_d = bounce_rd[0] * nx + bounce_rd[1] * ny + bounce_rd[2] * nz
        if n_dot_d < 0.0:
            bounce_rd[0] = -bounce_rd[0]
            bounce_rd[1] = -bounce_rd[1]
            bounce_rd[2] = -bounce_rd[2]

        bounce_r, bounce_g, bounce_b = trace_ray(
            bounce_ro,
            bounce_rd,
            lx,
            ly,
            lz,
            bounces - 1,
            ambient_on,
            sky_on,
            soft_shadow_on,
            hard_shadow_on,
            reflection_on,
            refraction_on,
            diffuse_gi_strength,
            spheres,
            boxes,
            plane_h,
        )

        r += base_r * bounce_r * diffuse_gi_strength
        g += base_g * bounce_g * diffuse_gi_strength
        b += base_b * bounce_b * diffuse_gi_strength

    r *= diffuse_weight
    g *= diffuse_weight
    b *= diffuse_weight

    if reflection_on == 1 and bounces > 0 and reflectivity > 0.0:
        rx, ry, rz = reflect_components(rd[0], rd[1], rd[2], nx, ny, nz)

        reflected_ro = np.empty(3, dtype=np.float32)
        reflected_rd = np.empty(3, dtype=np.float32)

        reflected_ro[0] = hit_x + nx * HIT_BIAS
        reflected_ro[1] = hit_y + ny * HIT_BIAS
        reflected_ro[2] = hit_z + nz * HIT_BIAS

        reflected_rd[0] = rx
        reflected_rd[1] = ry
        reflected_rd[2] = rz

        reflected_r, reflected_g, reflected_b = trace_ray(
            reflected_ro,
            reflected_rd,
            lx,
            ly,
            lz,
            bounces - 1,
            ambient_on,
            sky_on,
            soft_shadow_on,
            hard_shadow_on,
            reflection_on,
            refraction_on,
            diffuse_gi_strength,
            spheres,
            boxes,
            plane_h,
        )

        # attenuation
        reflected_r *= base_r * 0.7
        reflected_g *= base_g * 0.7
        reflected_b *= base_b * 0.7

        r = r + reflected_r * reflectivity
        g = g + reflected_g * reflectivity
        b = b + reflected_b * reflectivity

    return r, g, b