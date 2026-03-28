import math
import numpy as np
from numba import njit

from geometry.sphere import hit_sphere
from geometry.box import hit_box
from geometry.plane import hit_plane
from lighting import local_lighting, reflect
from materials import MATERIALS


@njit
def trace(ro, rd, sphere_x, sphere_y, sphere_z, sphere_r, box_x, box_y, box_z, box_sx, box_sy, box_sz, plane_h):
    t_min = -1.0
    mat = -1

    t = hit_sphere(ro, rd, sphere_x, sphere_y, sphere_z, sphere_r)
    if t > 0.0:
        t_min = t
        mat = 1

    t = hit_box(ro, rd, box_x, box_y, box_z, box_sx, box_sy, box_sz)
    if t > 0.0 and (t_min < 0.0 or t < t_min):
        t_min = t
        mat = 2

    t = hit_plane(ro, rd, plane_h)
    if t > 0.0 and (t_min < 0.0 or t < t_min):
        t_min = t
        mat = 0

    return t_min, mat


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
    sphere_x, sphere_y, sphere_z, sphere_r,
    box_x, box_y, box_z, box_sx, box_sy, box_sz,
    plane_h,
):
    eps = 1e-3
    shadow_ro = (hit_x + nx * eps, hit_y + ny * eps, hit_z + nz * eps)

    if soft_shadow_on == 1:
        visible = 0.0
        samples = 4
        for _ in range(samples):
            jitter_x = light[0] + ((np.random.rand() - 0.5) * 0.1)
            jitter_y = light[1] + ((np.random.rand() - 0.5) * 0.1)
            jitter_z = light[2] + ((np.random.rand() - 0.5) * 0.1)

            jitter_len = math.sqrt(jitter_x * jitter_x + jitter_y * jitter_y + jitter_z * jitter_z)
            jitter_light = (jitter_x / jitter_len, jitter_y / jitter_len, jitter_z / jitter_len)

            t_shadow, _ = trace(
                shadow_ro, jitter_light,
                sphere_x, sphere_y, sphere_z, sphere_r,
                box_x, box_y, box_z, box_sx, box_sy, box_sz,
                plane_h,
            )
            if t_shadow < 0.0:
                visible += 1.0

        return visible / samples

    if hard_shadow_on == 1:
        t_shadow, _ = trace(
            shadow_ro, light,
            sphere_x, sphere_y, sphere_z, sphere_r,
            box_x, box_y, box_z, box_sx, box_sy, box_sz,
            plane_h,
        )
        return 0.0 if t_shadow > 0.0 else 1.0

    return 1.0


@njit
def trace_ray(
    ro, rd, light, bounces,
    ambient_on, sky_on, soft_shadow_on, hard_shadow_on,
    reflection_on, refraction_on,
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
        if sky_on == 1:
            return 0.2 + 0.5 * (rd[1] * 0.5 + 0.5)
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
        sphere_x, sphere_y, sphere_z, sphere_r,
        box_x, box_y, box_z, box_sx, box_sy, box_sz,
        plane_h,
    )

    local_color = local_lighting(rd, normal, light, mat_id, lambert, shadow, ambient_on)
    color = local_color

    reflectivity = MATERIALS[mat_id, 3]
    roughness = MATERIALS[mat_id, 4]
    refractivity = MATERIALS[mat_id, 5]
    eps = 1e-3

    reflection_component = 0.0
    if reflection_on == 1 and bounces > 0 and reflectivity > 0.0:
        rx, ry, rz = reflect(rd, normal)

        if roughness > 0.0:
            jx, jy, jz = random_unit_vector()
            rx += jx * roughness
            ry += jy * roughness
            rz += jz * roughness

        r_len = math.sqrt(rx * rx + ry * ry + rz * rz)
        if r_len > 0.0:
            inv = 1.0 / r_len
            rx *= inv
            ry *= inv
            rz *= inv

        reflected = trace_ray(
            (hit_x + nx * eps, hit_y + ny * eps, hit_z + nz * eps),
            (rx, ry, rz),
            light,
            bounces - 1,
            ambient_on, sky_on, soft_shadow_on, hard_shadow_on,
            reflection_on, refraction_on,
            sphere_x, sphere_y, sphere_z, sphere_r,
            box_x, box_y, box_z, box_sx, box_sy, box_sz,
            plane_h,
        )
        color = (1.0 - reflectivity) * local_color + reflectivity * reflected
        reflection_component = reflectivity * reflected

    if refraction_on == 1 and bounces > 0 and refractivity > 0.0:
        eta = 1.0 / 1.3
        cosi = -(rd[0] * nx + rd[1] * ny + rd[2] * nz)
        k = 1.0 - eta * eta * (1.0 - cosi * cosi)

        if k > 0.0:
            refr_x = eta * rd[0] + (eta * cosi - math.sqrt(k)) * nx
            refr_y = eta * rd[1] + (eta * cosi - math.sqrt(k)) * ny
            refr_z = eta * rd[2] + (eta * cosi - math.sqrt(k)) * nz

            refr_len = math.sqrt(refr_x * refr_x + refr_y * refr_y + refr_z * refr_z)
            if refr_len > 0.0:
                inv = 1.0 / refr_len
                refr_x *= inv
                refr_y *= inv
                refr_z *= inv

                refracted = trace_ray(
                    (hit_x - nx * eps, hit_y - ny * eps, hit_z - nz * eps),
                    (refr_x, refr_y, refr_z),
                    light,
                    bounces - 1,
                    ambient_on, sky_on, soft_shadow_on, hard_shadow_on,
                    reflection_on, refraction_on,
                    sphere_x, sphere_y, sphere_z, sphere_r,
                    box_x, box_y, box_z, box_sx, box_sy, box_sz,
                    plane_h,
                )
                color += refracted * refractivity

    _ = reflection_component
    return color