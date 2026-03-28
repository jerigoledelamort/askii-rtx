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
REFLECT_ATTEN = np.float32(0.6)

_rng_states = None
_rng_size = 0


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


@cuda.jit
def render_kernel(
    buffer_idx,
    buffer_rgb,
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
    chars_len,
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
    exposure,
    gamma,
    materials,
    rng_states,
):
    x, y = cuda.grid(2)
    if x >= W or y >= H:
        return

    thread_id = y * W + x

    out_r = 0.0
    out_g = 0.0
    out_b = 0.0

    for _ in range(samples):
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
        diffuse_done = 0

        for _bounce in range(bounces):
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

            lambert = nx * lx + ny * ly + nz * lz
            if lambert < 0.0:
                lambert = 0.0

            shadow = compute_shadow(hit_x, hit_y, hit_z, nx, ny, nz, lx, ly, lz, soft_shadow_on, hard_shadow_on, spheres, boxes, plane_h, rng_states, thread_id)
            lighting = local_lighting(rd_x, rd_y, rd_z, nx, ny, nz, lx, ly, lz, mat_id, lambert, shadow, materials, ambient_on)

            base_r = materials[mat_id, 6]
            base_g = materials[mat_id, 7]
            base_b = materials[mat_id, 8]
            reflectivity = materials[mat_id, 3]
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

            if refraction_on == 1 and refractivity > 0.0:
                ior = 1.0 + refractivity * 0.7
                tx, ty, tz, ok = refract_components(rd_x, rd_y, rd_z, nx, ny, nz, ior)
                if ok == 1:
                    next_rd_x = tx
                    next_rd_y = ty
                    next_rd_z = tz
                    throughput_r *= base_r * (0.55 + 0.45 * refractivity)
                    throughput_g *= base_g * (0.55 + 0.45 * refractivity)
                    throughput_b *= base_b * (0.55 + 0.45 * refractivity)
                    continue_path = 1
                elif reflection_on == 1 and reflectivity > 0.0:
                    rx, ry, rz = reflect_components(rd_x, rd_y, rd_z, nx, ny, nz)
                    next_rd_x = rx
                    next_rd_y = ry
                    next_rd_z = rz
                    throughput_r *= base_r * REFLECT_ATTEN * reflectivity
                    throughput_g *= base_g * REFLECT_ATTEN * reflectivity
                    throughput_b *= base_b * REFLECT_ATTEN * reflectivity
                    continue_path = 1

            if continue_path == 0 and reflection_on == 1 and reflectivity > 0.0:
                rand = xoroshiro128p_uniform_float32(rng_states, thread_id)
                if rand < reflectivity:
                    rx, ry, rz = reflect_components(rd_x, rd_y, rd_z, nx, ny, nz)
                    next_rd_x = rx
                    next_rd_y = ry
                    next_rd_z = rz
                    throughput_r *= base_r * REFLECT_ATTEN * reflectivity
                    throughput_g *= base_g * REFLECT_ATTEN * reflectivity
                    throughput_b *= base_b * REFLECT_ATTEN * reflectivity
                else:
                    dx, dy, dz = random_hemisphere(nx, ny, nz, rng_states, thread_id)
                    next_rd_x = dx
                    next_rd_y = dy
                    next_rd_z = dz
                    throughput_r *= base_r * diffuse_gi_strength
                    throughput_g *= base_g * diffuse_gi_strength
                    throughput_b *= base_b * diffuse_gi_strength
                    diffuse_done = 1
                continue_path = 1

            if continue_path == 0 and diffuse_done == 0:
                dx, dy, dz = random_hemisphere(nx, ny, nz, rng_states, thread_id)
                next_rd_x = dx
                next_rd_y = dy
                next_rd_z = dz
                inv_prob = 1.0 - reflectivity
                if inv_prob < 1e-6:
                    inv_prob = 1e-6

                throughput_r *= base_r * diffuse_gi_strength / inv_prob
                throughput_g *= base_g * diffuse_gi_strength / inv_prob
                throughput_b *= base_b * diffuse_gi_strength / inv_prob
                diffuse_done = 1
                continue_path = 1

            if continue_path == 0:
                break

            ro_x = next_ro_x
            ro_y = next_ro_y
            ro_z = next_ro_z
            rd_x = next_rd_x
            rd_y = next_rd_y
            rd_z = next_rd_z

            if _bounce > 2:
                rr = max(throughput_r, throughput_g, throughput_b)
                if rr < 1e-6:
                    break
                if xoroshiro128p_uniform_float32(rng_states, thread_id) > rr:
                    break
                inv_rr = 1.0 / rr
                throughput_r *= inv_rr
                throughput_g *= inv_rr
                throughput_b *= inv_rr

        out_r += accum_r
        out_g += accum_g
        out_b += accum_b

    inv_samples = 1.0 / samples
    r = out_r * inv_samples * exposure
    g = out_g * inv_samples * exposure
    b = out_b * inv_samples * exposure

    if gamma != 1.0:
        r = r ** gamma
        g = g ** gamma
        b = b ** gamma

    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if luminance < 0.0:
        luminance = 0.0
    elif luminance > 1.0:
        luminance = 1.0

    max_c = max(r, g, b, 1e-6)
    nr = r / max_c
    ng = g / max_c
    nb = b / max_c

    if nr < 0.0:
        nr = 0.0
    elif nr > 1.0:
        nr = 1.0
    if ng < 0.0:
        ng = 0.0
    elif ng > 1.0:
        ng = 1.0
    if nb < 0.0:
        nb = 0.0
    elif nb > 1.0:
        nb = 1.0

    buffer_idx[y, x] = int(luminance * (chars_len - 1))
    buffer_rgb[y, x, 0] = nr
    buffer_rgb[y, x, 1] = ng
    buffer_rgb[y, x, 2] = nb


def render_frame_buffer(W, H, aspect, scene_time, camera_angle, dt, chars):
    _ = dt
    global _rng_states, _rng_size

    light = get_light()

    samples = int(config.RENDER["samples"])
    bounces = int(config.RENDER["bounces"])

    ambient_on = int(config.LIGHTING["ambient"])
    sky_on = int(config.LIGHTING["sky"])
    soft_shadow_on = int(config.LIGHTING["soft_shadows"])
    hard_shadow_on = int(config.LIGHTING["hard_shadows"])
    reflection_on = int(config.LIGHTING["reflections"])
    refraction_on = int(config.LIGHTING["refraction"])

    exposure = np.float32(config.RENDER.get("exposure", 1.0))
    gamma = np.float32(config.RENDER.get("gamma", 1.0))
    diffuse_gi_strength = np.float32(config.RENDER.get("diffuse_gi_strength", 0.25))

    ro, forward, right, up = get_camera(camera_angle)
    spheres, boxes, plane_y = get_scene_flat(scene_time)

    buffer_idx = np.zeros((H, W), dtype=np.int32)
    buffer_rgb = np.zeros((H, W, 3), dtype=np.float32)

    d_buffer_idx = cuda.to_device(buffer_idx)
    d_buffer_rgb = cuda.to_device(buffer_rgb)

    d_spheres = cuda.to_device(spheres.astype(np.float32))
    d_boxes = cuda.to_device(boxes.astype(np.float32))
    d_materials = cuda.to_device(MATERIALS.astype(np.float32))
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

    render_kernel[blocks, threads](
        d_buffer_idx,
        d_buffer_rgb,
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
        len(chars),
        np.float32(light[0]),
        np.float32(light[1]),
        np.float32(light[2]),
        d_ro,
        d_forward,
        d_right,
        d_up,
        d_spheres,
        d_boxes,
        np.float32(plane_y),
        diffuse_gi_strength,
        exposure,
        gamma,
        d_materials,
        rng_states,
    )
    cuda.synchronize()

    return d_buffer_idx.copy_to_host(), d_buffer_rgb.copy_to_host()


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