import math
import numpy as np
import pygame
from numba import cuda
from numba.cuda.random import create_xoroshiro128p_states, xoroshiro128p_uniform_float32

import config
from camera import get_camera
from scene import get_scene_flat
from lighting import get_light
from materials import MATERIALS


HIT_BIAS = np.float32(1e-3)
EPS = np.float32(1e-6)
DIRECT_WEIGHT = np.float32(0.8)
REFLECT_ATTEN = np.float32(0.7)
FOG_DENSITY = np.float32(0.12)
DITHER_STRENGTH = np.float32(0.01)
ADAPTIVE_VARIANCE_THRESHOLD = np.float32(0.03)
ADAPTIVE_MIN_SAMPLES = 1

_rng_states = None
_rng_size = 0

_d_spheres = None
_d_boxes = None
_d_materials = None
_prev_spheres = None
_prev_boxes = None
_prev_plane = None

_d_accum_rgb = None
_d_sample_count = None
_accum_shape = None
_prev_camera_state = None


def _camera_state(ro, forward, right, up):
    return np.concatenate((ro, forward, right, up)).astype(np.float32)


def _scene_changed(spheres, boxes, plane_y):
    global _prev_spheres, _prev_boxes, _prev_plane

    changed = (
        _prev_spheres is None
        or _prev_boxes is None
        or _prev_plane is None
        or _prev_spheres.shape != spheres.shape
        or _prev_boxes.shape != boxes.shape
        or not np.array_equal(_prev_spheres, spheres)
        or not np.array_equal(_prev_boxes, boxes)
        or float(_prev_plane) != float(plane_y)
    )

    if changed:
        _prev_spheres = spheres.copy()
        _prev_boxes = boxes.copy()
        _prev_plane = float(plane_y)

    return changed


def _ensure_device_scene(spheres, boxes):
    global _d_spheres, _d_boxes, _d_materials

    if _d_spheres is None or _d_spheres.shape != spheres.shape:
        _d_spheres = cuda.to_device(spheres.astype(np.float32))
    else:
        _d_spheres.copy_to_device(spheres.astype(np.float32))

    if _d_boxes is None or _d_boxes.shape != boxes.shape:
        _d_boxes = cuda.to_device(boxes.astype(np.float32))
    else:
        _d_boxes.copy_to_device(boxes.astype(np.float32))

    if _d_materials is None:
        _d_materials = cuda.to_device(MATERIALS.astype(np.float32))


def _reset_accumulation(W, H):
    global _d_accum_rgb, _d_sample_count, _accum_shape
    _d_accum_rgb = cuda.to_device(np.zeros((H, W, 3), dtype=np.float32))
    _d_sample_count = cuda.to_device(np.zeros((H, W), dtype=np.float32))
    _accum_shape = (H, W)


@cuda.jit(device=True)
def saturate01(x):
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


@cuda.jit(device=True)
def luminance_of(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


@cuda.jit(device=True)
def reflect_components(dx, dy, dz, nx, ny, nz):
    dot = dx * nx + dy * ny + dz * nz
    return (
        dx - 2.0 * dot * nx,
        dy - 2.0 * dot * ny,
        dz - 2.0 * dot * nz,
    )


@cuda.jit(device=True)
def refract_components(dx, dy, dz, nx, ny, nz, ior):
    cosi = dx * nx + dy * ny + dz * nz
    etai = 1.0
    etat = ior
    nnx = nx
    nny = ny
    nnz = nz

    if cosi < 0.0:
        cosi = -cosi
    else:
        tmp = etai
        etai = etat
        etat = tmp
        nnx = -nx
        nny = -ny
        nnz = -nz

    eta = etai / etat
    k = 1.0 - eta * eta * (1.0 - cosi * cosi)
    if k < 0.0:
        return 0.0, 0.0, 0.0, 0

    rx = eta * dx + (eta * cosi - math.sqrt(k)) * nnx
    ry = eta * dy + (eta * cosi - math.sqrt(k)) * nny
    rz = eta * dz + (eta * cosi - math.sqrt(k)) * nnz

    rl = math.sqrt(rx * rx + ry * ry + rz * rz)
    if rl > EPS:
        inv = 1.0 / rl
        rx *= inv
        ry *= inv
        rz *= inv
    return rx, ry, rz, 1


@cuda.jit(device=True)
def schlick(f0, cos_theta):
    c = 1.0 - cos_theta
    return f0 + (1.0 - f0) * c * c * c * c * c


@cuda.jit(device=True)
def hit_sphere(ro_x, ro_y, ro_z, rd_x, rd_y, rd_z, cx, cy, cz, radius):
    ocx = ro_x - cx
    ocy = ro_y - cy
    ocz = ro_z - cz

    a = rd_x * rd_x + rd_y * rd_y + rd_z * rd_z
    b = 2.0 * (ocx * rd_x + ocy * rd_y + ocz * rd_z)
    c = ocx * ocx + ocy * ocy + ocz * ocz - radius * radius

    disc = b * b - 4.0 * a * c
    if disc < 0.0:
        return -1.0

    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) / (2.0 * a)
    t2 = (-b + sqrt_disc) / (2.0 * a)

    if t1 > 0.0:
        return t1
    if t2 > 0.0:
        return t2
    return -1.0


@cuda.jit(device=True)
def hit_box(ro_x, ro_y, ro_z, rd_x, rd_y, rd_z, cx, cy, cz, sx, sy, sz):
    min_x = cx - sx
    min_y = cy - sy
    min_z = cz - sz
    max_x = cx + sx
    max_y = cy + sy
    max_z = cz + sz

    tmin = -1e9
    tmax = 1e9

    if abs(rd_x) < EPS:
        if ro_x < min_x or ro_x > max_x:
            return -1.0
    else:
        t1 = (min_x - ro_x) / rd_x
        t2 = (max_x - ro_x) / rd_x
        lo = t1 if t1 < t2 else t2
        hi = t2 if t2 > t1 else t1
        tmin = lo if lo > tmin else tmin
        tmax = hi if hi < tmax else tmax
        if tmax < tmin:
            return -1.0

    if abs(rd_y) < EPS:
        if ro_y < min_y or ro_y > max_y:
            return -1.0
    else:
        t1 = (min_y - ro_y) / rd_y
        t2 = (max_y - ro_y) / rd_y
        lo = t1 if t1 < t2 else t2
        hi = t2 if t2 > t1 else t1
        tmin = lo if lo > tmin else tmin
        tmax = hi if hi < tmax else tmax
        if tmax < tmin:
            return -1.0

    if abs(rd_z) < EPS:
        if ro_z < min_z or ro_z > max_z:
            return -1.0
    else:
        t1 = (min_z - ro_z) / rd_z
        t2 = (max_z - ro_z) / rd_z
        lo = t1 if t1 < t2 else t2
        hi = t2 if t2 > t1 else t1
        tmin = lo if lo > tmin else tmin
        tmax = hi if hi < tmax else tmax
        if tmax < tmin:
            return -1.0

    if tmin > 0.0:
        return tmin
    return tmax if tmax > 0.0 else -1.0


@cuda.jit(device=True)
def trace_scene(ro_x, ro_y, ro_z, rd_x, rd_y, rd_z, spheres, boxes, plane_h):
    t_min = -1.0
    mat = -1
    hit_type = -1
    hit_index = -1

    for i in range(spheres.shape[0]):
        t = hit_sphere(ro_x, ro_y, ro_z, rd_x, rd_y, rd_z, spheres[i, 0], spheres[i, 1], spheres[i, 2], spheres[i, 3])
        if t > 0.0 and (t_min < 0.0 or t < t_min):
            t_min = t
            mat = int(spheres[i, 4])
            hit_type = 1
            hit_index = i

    for i in range(boxes.shape[0]):
        t = hit_box(ro_x, ro_y, ro_z, rd_x, rd_y, rd_z, boxes[i, 0], boxes[i, 1], boxes[i, 2], boxes[i, 3], boxes[i, 4], boxes[i, 5])
        if t > 0.0 and (t_min < 0.0 or t < t_min):
            t_min = t
            mat = int(boxes[i, 6])
            hit_type = 2
            hit_index = i

    if abs(rd_y) >= EPS:
        t = (plane_h - ro_y) / rd_y
        if t > 0.0 and (t_min < 0.0 or t < t_min):
            t_min = t
            mat = 0
            hit_type = 0
            hit_index = -1

    return t_min, mat, hit_type, hit_index


@cuda.jit(device=True)
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
    if length > EPS:
        inv = 1.0 / length
        return nx * inv, ny * inv, nz * inv
    return 0.0, 1.0, 0.0


@cuda.jit(device=True)
def local_lighting(rd_x, rd_y, rd_z, nx, ny, nz, lx, ly, lz, mat_id, lambert, shadow, materials, ambient_on):
    diffuse_strength = materials[mat_id, 0]
    specular_strength = materials[mat_id, 1]
    shininess = materials[mat_id, 2]

    ambient = 0.05 if ambient_on == 1 else 0.0
    diffuse = diffuse_strength * lambert * shadow

    view_x = -rd_x
    view_y = -rd_y
    view_z = -rd_z

    rlx, rly, rlz = reflect_components(lx, ly, lz, nx, ny, nz)
    spec_angle = view_x * rlx + view_y * rly + view_z * rlz
    if spec_angle < 0.0:
        spec_angle = 0.0

    specular = specular_strength * (spec_angle ** shininess) * shadow
    return ambient + diffuse + specular


@cuda.jit(device=True)
def compute_shadow(hit_x, hit_y, hit_z, nx, ny, nz, lx, ly, lz, soft_shadow_on, hard_shadow_on, spheres, boxes, plane_h, rng_states, thread_id):
    shadow_ro_x = hit_x + nx * HIT_BIAS
    shadow_ro_y = hit_y + ny * HIT_BIAS
    shadow_ro_z = hit_z + nz * HIT_BIAS

    if soft_shadow_on == 1:
        visible = 0.0
        samples = 4
        for _ in range(samples):
            jitter_x = lx + (xoroshiro128p_uniform_float32(rng_states, thread_id) - 0.5) * 0.1
            jitter_y = ly + (xoroshiro128p_uniform_float32(rng_states, thread_id) - 0.5) * 0.1
            jitter_z = lz + (xoroshiro128p_uniform_float32(rng_states, thread_id) - 0.5) * 0.1
            jl = math.sqrt(jitter_x * jitter_x + jitter_y * jitter_y + jitter_z * jitter_z)
            if jl > EPS:
                inv = 1.0 / jl
                jitter_x *= inv
                jitter_y *= inv
                jitter_z *= inv
            t_shadow, _, _, _ = trace_scene(shadow_ro_x, shadow_ro_y, shadow_ro_z, jitter_x, jitter_y, jitter_z, spheres, boxes, plane_h)
            if t_shadow < 0.0:
                visible += 1.0
        return visible / samples

    if hard_shadow_on == 1:
        t_shadow, _, _, _ = trace_scene(shadow_ro_x, shadow_ro_y, shadow_ro_z, lx, ly, lz, spheres, boxes, plane_h)
        return 0.0 if t_shadow > 0.0 else 1.0

    return 1.0


@cuda.jit(device=True)
def random_hemisphere(nx, ny, nz, rng_states, thread_id):
    rx = nx + (xoroshiro128p_uniform_float32(rng_states, thread_id) - 0.5)
    ry = ny + (xoroshiro128p_uniform_float32(rng_states, thread_id) - 0.5)
    rz = nz + (xoroshiro128p_uniform_float32(rng_states, thread_id) - 0.5)

    dl = math.sqrt(rx * rx + ry * ry + rz * rz)
    if dl > EPS:
        inv = 1.0 / dl
        rx *= inv
        ry *= inv
        rz *= inv

    n_dot_d = rx * nx + ry * ny + rz * nz
    if n_dot_d < 0.0:
        rx = -rx
        ry = -ry
        rz = -rz

    return rx, ry, rz


@cuda.jit(device=True)
def aces_tonemap(x):
    a = 2.51
    b = 0.03
    c = 2.43
    d = 0.59
    e = 0.14
    y = (x * (a * x + b)) / (x * (c * x + d) + e)
    return saturate01(y)


@cuda.jit
def render_sample_kernel(
    sample_rgb,
    sample_depth,
    sample_normal,
    sample_used,
    W,
    H,
    aspect,
    samples,
    bounces,
    ambient_on,
    sky_on,
    soft_shadow_on,
    hard_shadow_on,
    reflection_on,
    refraction_on,
    fresnel_on,
    lx,
    ly,
    lz,
    ro,
    forward,
    right,
    up,
    spheres,
    boxes,
    plane_h,
    diffuse_gi_strength,
    materials,
    rng_states,
    accum_rgb,
    sample_count,
):
    x, y = cuda.grid(2)
    if x >= W or y >= H:
        return

    thread_id = y * W + x

    prev_count = sample_count[y, x]
    prev_lum = 0.0
    if prev_count > 0.0:
        prev_r = accum_rgb[y, x, 0] / prev_count
        prev_g = accum_rgb[y, x, 1] / prev_count
        prev_b = accum_rgb[y, x, 2] / prev_count
        prev_lum = luminance_of(prev_r, prev_g, prev_b)

    target_samples = samples
    if prev_count > 0.0 and samples > ADAPTIVE_MIN_SAMPLES:
        target_samples = samples

    out_r = 0.0
    out_g = 0.0
    out_b = 0.0
    depth_sum = 0.0
    nsum_x = 0.0
    nsum_y = 0.0
    nsum_z = 0.0
    used = 0

    for _sample in range(samples):
        if _sample >= target_samples:
            break

        nxs = ((x + xoroshiro128p_uniform_float32(rng_states, thread_id)) / W) * 2.0 - 1.0
        nys = 1.0 - ((y + xoroshiro128p_uniform_float32(rng_states, thread_id)) / H) * 2.0
        nxs *= aspect

        rd_x = forward[0] + right[0] * nxs + up[0] * nys
        rd_y = forward[1] + right[1] * nxs + up[1] * nys
        rd_z = forward[2] + right[2] * nxs + up[2] * nys
        rl = math.sqrt(rd_x * rd_x + rd_y * rd_y + rd_z * rd_z)
        if rl > EPS:
            inv = 1.0 / rl
            rd_x *= inv
            rd_y *= inv
            rd_z *= inv

        ro_x = ro[0]
        ro_y = ro[1]
        ro_z = ro[2]

        throughput_r = 1.0
        throughput_g = 1.0
        throughput_b = 1.0
        accum_r = 0.0
        accum_g = 0.0
        accum_b = 0.0
        first_depth = -1.0
        first_nx = 0.0
        first_ny = 1.0
        first_nz = 0.0

        for bounce in range(bounces):
            t, mat_id, hit_type, hit_index = trace_scene(ro_x, ro_y, ro_z, rd_x, rd_y, rd_z, spheres, boxes, plane_h)

            if t < 0.0:
                if sky_on == 1:
                    sky = 0.2 + 0.5 * (rd_y * 0.5 + 0.5)
                    accum_r += throughput_r * sky
                    accum_g += throughput_g * sky
                    accum_b += throughput_b * sky
                break

            hit_x = ro_x + rd_x * t
            hit_y = ro_y + rd_y * t
            hit_z = ro_z + rd_z * t
            nx, ny, nz = get_normal(hit_x, hit_y, hit_z, hit_type, hit_index, spheres, boxes)

            if bounce == 0:
                first_depth = t
                first_nx = nx
                first_ny = ny
                first_nz = nz

            lambert = nx * lx + ny * ly + nz * lz
            if lambert < 0.0:
                lambert = 0.0

            shadow = compute_shadow(hit_x, hit_y, hit_z, nx, ny, nz, lx, ly, lz, soft_shadow_on, hard_shadow_on, spheres, boxes, plane_h, rng_states, thread_id)
            lighting = local_lighting(rd_x, rd_y, rd_z, nx, ny, nz, lx, ly, lz, mat_id, lambert, shadow, materials, ambient_on)

            base_r = materials[mat_id, 6]
            base_g = materials[mat_id, 7]
            base_b = materials[mat_id, 8]
            reflectivity = materials[mat_id, 3]
            roughness = materials[mat_id, 4]
            refractivity = materials[mat_id, 5]

            local_r = base_r * lighting
            local_g = base_g * lighting
            local_b = base_b * lighting

            accum_r += throughput_r * local_r * DIRECT_WEIGHT
            accum_g += throughput_g * local_g * DIRECT_WEIGHT
            accum_b += throughput_b * local_b * DIRECT_WEIGHT

            next_ro_x = hit_x + nx * HIT_BIAS
            next_ro_y = hit_y + ny * HIT_BIAS
            next_ro_z = hit_z + nz * HIT_BIAS
            next_rd_x = rd_x
            next_rd_y = rd_y
            next_rd_z = rd_z
            continue_path = 0

            cos_theta = -(rd_x * nx + rd_y * ny + rd_z * nz)
            if cos_theta < 0.0:
                cos_theta = 0.0
            if cos_theta > 1.0:
                cos_theta = 1.0

            fresnel = reflectivity
            if fresnel_on == 1:
                fresnel = schlick(reflectivity, cos_theta)

            diffuse_weight = 1.0 - fresnel
            if diffuse_weight < 0.0:
                diffuse_weight = 0.0

            if refraction_on == 1 and refractivity > 0.0:
                ior = 1.0 + refractivity * 0.5
                f0r = (1.0 - ior) / (1.0 + ior)
                f0r = f0r * f0r
                fresnel_refract = schlick(f0r, cos_theta)

                tx, ty, tz, ok = refract_components(rd_x, rd_y, rd_z, nx, ny, nz, ior)
                use_reflect = 0
                if ok == 0:
                    use_reflect = 1
                else:
                    if xoroshiro128p_uniform_float32(rng_states, thread_id) < fresnel_refract:
                        use_reflect = 1

                if use_reflect == 1 and reflection_on == 1:
                    rx, ry, rz = reflect_components(rd_x, rd_y, rd_z, nx, ny, nz)
                    jx, jy, jz = random_hemisphere(nx, ny, nz, rng_states, thread_id)
                    next_rd_x = rx + jx * roughness
                    next_rd_y = ry + jy * roughness
                    next_rd_z = rz + jz * roughness
                    nl = math.sqrt(next_rd_x * next_rd_x + next_rd_y * next_rd_y + next_rd_z * next_rd_z)
                    if nl > EPS:
                        inv_nl = 1.0 / nl
                        next_rd_x *= inv_nl
                        next_rd_y *= inv_nl
                        next_rd_z *= inv_nl
                    throughput_r *= base_r * REFLECT_ATTEN * fresnel_refract
                    throughput_g *= base_g * REFLECT_ATTEN * fresnel_refract
                    throughput_b *= base_b * REFLECT_ATTEN * fresnel_refract
                else:
                    next_rd_x = tx
                    next_rd_y = ty
                    next_rd_z = tz
                    trans = 1.0 - fresnel_refract
                    throughput_r *= base_r * trans
                    throughput_g *= base_g * trans
                    throughput_b *= base_b * trans
                continue_path = 1

            if continue_path == 0 and reflection_on == 1 and reflectivity > 0.0:
                if xoroshiro128p_uniform_float32(rng_states, thread_id) < fresnel:
                    rx, ry, rz = reflect_components(rd_x, rd_y, rd_z, nx, ny, nz)
                    jx, jy, jz = random_hemisphere(nx, ny, nz, rng_states, thread_id)
                    next_rd_x = rx + jx * roughness
                    next_rd_y = ry + jy * roughness
                    next_rd_z = rz + jz * roughness
                    nl = math.sqrt(next_rd_x * next_rd_x + next_rd_y * next_rd_y + next_rd_z * next_rd_z)
                    if nl > EPS:
                        inv_nl = 1.0 / nl
                        next_rd_x *= inv_nl
                        next_rd_y *= inv_nl
                        next_rd_z *= inv_nl
                    throughput_r *= base_r * REFLECT_ATTEN * fresnel
                    throughput_g *= base_g * REFLECT_ATTEN * fresnel
                    throughput_b *= base_b * REFLECT_ATTEN * fresnel
                else:
                    dx, dy, dz = random_hemisphere(nx, ny, nz, rng_states, thread_id)
                    next_rd_x = dx
                    next_rd_y = dy
                    next_rd_z = dz
                    throughput_r *= base_r * diffuse_gi_strength * diffuse_weight
                    throughput_g *= base_g * diffuse_gi_strength * diffuse_weight
                    throughput_b *= base_b * diffuse_gi_strength * diffuse_weight
                continue_path = 1

            if continue_path == 0:
                dx, dy, dz = random_hemisphere(nx, ny, nz, rng_states, thread_id)
                next_rd_x = dx
                next_rd_y = dy
                next_rd_z = dz
                throughput_r *= base_r * diffuse_gi_strength * diffuse_weight
                throughput_g *= base_g * diffuse_gi_strength * diffuse_weight
                throughput_b *= base_b * diffuse_gi_strength * diffuse_weight
                continue_path = 1

            ro_x = next_ro_x
            ro_y = next_ro_y
            ro_z = next_ro_z
            rd_x = next_rd_x
            rd_y = next_rd_y
            rd_z = next_rd_z

            if bounce >= 2:
                rr = luminance_of(throughput_r, throughput_g, throughput_b)
                if rr < 1e-5:
                    break
                rr = rr if rr < 0.95 else 0.95
                if xoroshiro128p_uniform_float32(rng_states, thread_id) > rr:
                    break
                inv_rr = 1.0 / rr
                throughput_r *= inv_rr
                throughput_g *= inv_rr
                throughput_b *= inv_rr

        out_r += accum_r
        out_g += accum_g
        out_b += accum_b
        depth_sum += first_depth if first_depth > 0.0 else 0.0
        nsum_x += first_nx
        nsum_y += first_ny
        nsum_z += first_nz
        used += 1

        if prev_count > 0.0 and used == 1 and samples > ADAPTIVE_MIN_SAMPLES:
            sample_lum = luminance_of(accum_r, accum_g, accum_b)
            variance = abs(sample_lum - prev_lum)
            if variance < ADAPTIVE_VARIANCE_THRESHOLD:
                target_samples = ADAPTIVE_MIN_SAMPLES

    if used == 0:
        sample_rgb[y, x, 0] = 0.0
        sample_rgb[y, x, 1] = 0.0
        sample_rgb[y, x, 2] = 0.0
        sample_depth[y, x] = 0.0
        sample_normal[y, x, 0] = 0.0
        sample_normal[y, x, 1] = 1.0
        sample_normal[y, x, 2] = 0.0
        sample_used[y, x] = 0.0
        return

    inv_used = 1.0 / used
    sample_rgb[y, x, 0] = out_r * inv_used
    sample_rgb[y, x, 1] = out_g * inv_used
    sample_rgb[y, x, 2] = out_b * inv_used
    sample_depth[y, x] = depth_sum * inv_used

    nn = math.sqrt(nsum_x * nsum_x + nsum_y * nsum_y + nsum_z * nsum_z)
    if nn > EPS:
        inv_nn = 1.0 / nn
        sample_normal[y, x, 0] = nsum_x * inv_nn
        sample_normal[y, x, 1] = nsum_y * inv_nn
        sample_normal[y, x, 2] = nsum_z * inv_nn
    else:
        sample_normal[y, x, 0] = 0.0
        sample_normal[y, x, 1] = 1.0
        sample_normal[y, x, 2] = 0.0

    sample_used[y, x] = float(used)


@cuda.jit
def accumulate_kernel(accum_rgb, sample_count, sample_rgb, sample_used):
    x, y = cuda.grid(2)
    if x >= accum_rgb.shape[1] or y >= accum_rgb.shape[0]:
        return

    w = sample_used[y, x]
    if w <= 0.0:
        return

    accum_rgb[y, x, 0] += sample_rgb[y, x, 0] * w
    accum_rgb[y, x, 1] += sample_rgb[y, x, 1] * w
    accum_rgb[y, x, 2] += sample_rgb[y, x, 2] * w
    sample_count[y, x] += w


@cuda.jit
def postprocess_kernel(
    buffer_rgb,
    luminance_buffer,
    edge_buffer,
    accum_rgb,
    sample_count,
    depth_buffer,
    normal_buffer,
    W,
    H,
    exposure,
    gamma,
    fog_density,
    rng_states,
):
    x, y = cuda.grid(2)
    if x >= W or y >= H:
        return

    count = sample_count[y, x]
    if count <= 0.0:
        buffer_rgb[y, x, 0] = 0.0
        buffer_rgb[y, x, 1] = 0.0
        buffer_rgb[y, x, 2] = 0.0
        luminance_buffer[y, x] = 0.0
        edge_buffer[y, x] = 0.0
        return

    r = accum_rgb[y, x, 0] / count
    g = accum_rgb[y, x, 1] / count
    b = accum_rgb[y, x, 2] / count

    r *= exposure
    g *= exposure
    b *= exposure

    # Filmic (ACES) tonemapping
    r = aces_tonemap(r)
    g = aces_tonemap(g)
    b = aces_tonemap(b)

    if gamma != 1.0:
        r = r ** gamma
        g = g ** gamma
        b = b ** gamma

    # Slight saturation boost (stylization)
    lum = luminance_of(r, g, b)
    sat = 1.08
    r = lum + (r - lum) * sat
    g = lum + (g - lum) * sat
    b = lum + (b - lum) * sat

    depth = depth_buffer[y, x]
    if depth > 0.0:
        fog = 1.0 / (1.0 + depth * fog_density)
        r *= fog
        g *= fog
        b *= fog

    # Edge detection from depth + normal discontinuity
    edge = 0.0
    if x + 1 < W:
        d2 = depth_buffer[y, x + 1]
        if d2 > 0.0 and depth > 0.0:
            dd = abs(depth - d2) * 0.6
            if dd > edge:
                edge = dd
        nx0 = normal_buffer[y, x, 0]
        ny0 = normal_buffer[y, x, 1]
        nz0 = normal_buffer[y, x, 2]
        nx1 = normal_buffer[y, x + 1, 0]
        ny1 = normal_buffer[y, x + 1, 1]
        nz1 = normal_buffer[y, x + 1, 2]
        nd = 1.0 - (nx0 * nx1 + ny0 * ny1 + nz0 * nz1)
        if nd > edge:
            edge = nd

    if y + 1 < H:
        d2 = depth_buffer[y + 1, x]
        if d2 > 0.0 and depth > 0.0:
            dd = abs(depth - d2) * 0.6
            if dd > edge:
                edge = dd
        nx0 = normal_buffer[y, x, 0]
        ny0 = normal_buffer[y, x, 1]
        nz0 = normal_buffer[y, x, 2]
        nx1 = normal_buffer[y + 1, x, 0]
        ny1 = normal_buffer[y + 1, x, 1]
        nz1 = normal_buffer[y + 1, x, 2]
        nd = 1.0 - (nx0 * nx1 + ny0 * ny1 + nz0 * nz1)
        if nd > edge:
            edge = nd

    edge = saturate01(edge)
    # Dithering to reduce banding
    thread_id = y * W + x
    dither = (xoroshiro128p_uniform_float32(rng_states, thread_id) - 0.5) * (2.0 * DITHER_STRENGTH)

    lum = luminance_of(r, g, b)
    lum = lum + dither
    # higher contrast on edges
    lum = lum * (1.0 - 0.4 * edge) + edge * 0.9
    lum = saturate01(lum)

    r = saturate01(r)
    g = saturate01(g)
    b = saturate01(b)

    max_c = max(r, g, b, 1e-6)
    buffer_rgb[y, x, 0] = r / max_c
    buffer_rgb[y, x, 1] = g / max_c
    buffer_rgb[y, x, 2] = b / max_c
    luminance_buffer[y, x] = lum
    edge_buffer[y, x] = edge


def render_frame_buffer(W, H, aspect, scene_time, camera_angle, dt, chars):
    _ = dt
    global _rng_states, _rng_size, _prev_camera_state

    light = get_light()

    samples = int(config.RENDER["samples"])
    bounces = int(config.RENDER["bounces"])

    ambient_on = int(config.LIGHTING["ambient"])
    sky_on = int(config.LIGHTING["sky"])
    soft_shadow_on = int(config.LIGHTING["soft_shadows"])
    hard_shadow_on = int(config.LIGHTING["hard_shadows"])
    reflection_on = int(config.LIGHTING["reflections"])
    refraction_on = int(config.LIGHTING["refraction"])
    fresnel_on = int(config.LIGHTING.get("fresnel", 1))

    exposure = np.float32(config.RENDER.get("exposure", 1.0))
    gamma = np.float32(config.RENDER.get("gamma", 1.0))
    diffuse_gi_strength = np.float32(config.RENDER.get("diffuse_gi_strength", 0.25))

    ro, forward, right, up = get_camera(camera_angle)
    spheres, boxes, plane_y = get_scene_flat(scene_time)

    scene_changed = _scene_changed(spheres, boxes, plane_y)
    camera_state = _camera_state(ro, forward, right, up)
    camera_changed = _prev_camera_state is None or not np.allclose(_prev_camera_state, camera_state, atol=1e-6)
    _prev_camera_state = camera_state

    _ensure_device_scene(spheres, boxes)

    if _accum_shape != (H, W):
        _reset_accumulation(W, H)
    elif scene_changed or camera_changed:
        _reset_accumulation(W, H)

    sample_rgb = np.zeros((H, W, 3), dtype=np.float32)
    sample_depth = np.zeros((H, W), dtype=np.float32)
    sample_normal = np.zeros((H, W, 3), dtype=np.float32)
    sample_used = np.zeros((H, W), dtype=np.float32)

    luminance_buffer = np.zeros((H, W), dtype=np.float32)
    edge_buffer = np.zeros((H, W), dtype=np.float32)
    buffer_rgb = np.zeros((H, W, 3), dtype=np.float32)

    d_sample_rgb = cuda.to_device(sample_rgb)
    d_sample_depth = cuda.to_device(sample_depth)
    d_sample_normal = cuda.to_device(sample_normal)
    d_sample_used = cuda.to_device(sample_used)
    d_buffer_rgb = cuda.to_device(buffer_rgb)
    d_luminance = cuda.to_device(luminance_buffer)
    d_edge = cuda.to_device(edge_buffer)

    d_ro = cuda.to_device(ro.astype(np.float32))
    d_forward = cuda.to_device(forward.astype(np.float32))
    d_right = cuda.to_device(right.astype(np.float32))
    d_up = cuda.to_device(up.astype(np.float32))

    total_threads = W * H
    if _rng_states is None or _rng_size != total_threads:
        seed = np.random.randint(1, 1_000_000)
        _rng_states = create_xoroshiro128p_states(total_threads, seed=seed)
        _rng_size = total_threads
    rng_states = _rng_states

    threads = (16, 16)
    blocks = ((W + threads[0] - 1) // threads[0], (H + threads[1] - 1) // threads[1])

    render_sample_kernel[blocks, threads](
        d_sample_rgb,
        d_sample_depth,
        d_sample_normal,
        d_sample_used,
        W,
        H,
        np.float32(aspect),
        samples,
        bounces,
        ambient_on,
        sky_on,
        soft_shadow_on,
        hard_shadow_on,
        reflection_on,
        refraction_on,
        fresnel_on,
        np.float32(light[0]),
        np.float32(light[1]),
        np.float32(light[2]),
        d_ro,
        d_forward,
        d_right,
        d_up,
        _d_spheres,
        _d_boxes,
        np.float32(plane_y),
        diffuse_gi_strength,
        _d_materials,
        rng_states,
        _d_accum_rgb,
        _d_sample_count,
    )

    accumulate_kernel[blocks, threads](_d_accum_rgb, _d_sample_count, d_sample_rgb, d_sample_used)

    postprocess_kernel[blocks, threads](
        d_buffer_rgb,
        d_luminance,
        d_edge,
        _d_accum_rgb,
        _d_sample_count,
        d_sample_depth,
        d_sample_normal,
        W,
        H,
        exposure,
        gamma,
        FOG_DENSITY,
        rng_states,
    )
    cuda.synchronize()

    luminance_buffer = d_luminance.copy_to_host()
    edge_buffer = d_edge.copy_to_host()
    buffer_rgb = d_buffer_rgb.copy_to_host()

    # Adaptive character ramp from luminance histogram (vectorized, no Python pixel loops)
    hist, bin_edges = np.histogram(luminance_buffer, bins=max(8, min(128, len(chars))), range=(0.0, 1.0))
    cdf = np.cumsum(hist).astype(np.float32)
    if cdf[-1] > 0.0:
        cdf /= cdf[-1]
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        remapped = np.interp(luminance_buffer.ravel(), bin_centers, cdf).reshape(luminance_buffer.shape)
    else:
        remapped = luminance_buffer

    char_scale = float(len(chars) - 1)
    idx = np.clip((remapped * char_scale).astype(np.int32), 0, len(chars) - 1)

    strong_edge_idx = int(0.88 * char_scale)
    idx = np.where(edge_buffer > 0.28, np.maximum(idx, strong_edge_idx), idx)

    return idx.astype(np.int32), buffer_rgb


def draw_buffer(surface, buffer_idx, chars, char_cache, char_w, char_h, buffer_rgb=None):
    if buffer_rgb is None:
        for y, row in enumerate(buffer_idx):
            for x, idx in enumerate(row):
                char = chars[idx]
                surface.blit(char_cache[char], (x * char_w, y * char_h))
        return

    for y, row in enumerate(buffer_idx):
        for x, idx in enumerate(row):
            char = chars[idx]
            r = int(buffer_rgb[y, x, 0] * 255.0)
            g = int(buffer_rgb[y, x, 1] * 255.0)
            b = int(buffer_rgb[y, x, 2] * 255.0)
            glyph = char_cache.get((char, r, g, b))
            if glyph is None:
                glyph = pygame_font_render(char_cache, char, r, g, b)
                char_cache[(char, r, g, b)] = glyph
            surface.blit(glyph, (x * char_w, y * char_h))


def pygame_font_render(char_cache, char, r, g, b):
    font = char_cache["__font__"]
    return font.render(char, False, (r, g, b))