import math
import numpy as np
import pygame
from numba import cuda
from numba.cuda.random import create_xoroshiro128p_states, xoroshiro128p_uniform_float32

from engine.lighting import get_light
from engine.materials import MATERIALS


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

_d_accum_rgb = None
_d_sample_count = None
_accum_shape = None
_prev_camera_state = None


class RendererState:
    def __init__(self):
        self.rng_states = None
        self.rng_size = 0

        self.accum_rgb = None
        self.sample_count = None
        self.accum_shape = None

        self.prev_camera_state = None


def reset_accumulation_buffers():
    global _d_accum_rgb, _d_sample_count, _accum_shape, _prev_camera_state
    _d_accum_rgb = None
    _d_sample_count = None
    _accum_shape = None
    _prev_camera_state = None


def _camera_state(ro, forward, right, up):
    return np.concatenate((ro, forward, right, up)).astype(np.float32)


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


def _reset_accumulation(state, W, H):
    state.accum_rgb = cuda.to_device(np.zeros((H, W, 3), dtype=np.float32))
    state.sample_count = cuda.to_device(np.zeros((H, W), dtype=np.float32))
    state.accum_shape = (H, W)


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
def random_unit_vector(rng_states, thread_id):
    x = xoroshiro128p_uniform_float32(rng_states, thread_id) * 2.0 - 1.0
    y = xoroshiro128p_uniform_float32(rng_states, thread_id) * 2.0 - 1.0
    z = xoroshiro128p_uniform_float32(rng_states, thread_id) * 2.0 - 1.0

    ll = x * x + y * y + z * z
    if ll < EPS:
        return 0.0, 1.0, 0.0
    inv = 1.0 / math.sqrt(ll)
    return x * inv, y * inv, z * inv


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
def hit_triangle(
    ro_x, ro_y, ro_z,
    rd_x, rd_y, rd_z,
    v0x, v0y, v0z,
    v1x, v1y, v1z,
    v2x, v2y, v2z
):
    e1x = v1x - v0x
    e1y = v1y - v0y
    e1z = v1z - v0z

    e2x = v2x - v0x
    e2y = v2y - v0y
    e2z = v2z - v0z

    px = rd_y * e2z - rd_z * e2y
    py = rd_z * e2x - rd_x * e2z
    pz = rd_x * e2y - rd_y * e2x

    det = e1x * px + e1y * py + e1z * pz

    if abs(det) < EPS:
        return -1.0, 0.0, 0.0

    inv_det = 1.0 / det

    tx = ro_x - v0x
    ty = ro_y - v0y
    tz = ro_z - v0z

    u = (tx * px + ty * py + tz * pz) * inv_det
    if u < 0.0 or u > 1.0:
        return -1.0, 0.0, 0.0

    qx = ty * e1z - tz * e1y
    qy = tz * e1x - tx * e1z
    qz = tx * e1y - ty * e1x

    v = (rd_x * qx + rd_y * qy + rd_z * qz) * inv_det
    if v < 0.0 or (u + v) > 1.0:
        return -1.0, 0.0, 0.0

    t = (e2x * qx + e2y * qy + e2z * qz) * inv_det

    if t > 0.0:
        return t, u, v
    return -1.0, 0.0, 0.0


@cuda.jit(device=True)
def trace_scene(ro_x, ro_y, ro_z, rd_x, rd_y, rd_z, spheres, boxes, triangles, plane_h):
    t_min = -1.0
    hit_u = 0.0
    hit_v = 0.0
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
    
    for i in range(triangles.shape[0]):
        t, u, v = hit_triangle(
            ro_x, ro_y, ro_z,
            rd_x, rd_y, rd_z,
            triangles[i, 0], triangles[i, 1], triangles[i, 2],
            triangles[i, 3], triangles[i, 4], triangles[i, 5],
            triangles[i, 6], triangles[i, 7], triangles[i, 8],
        )

        if t > 0.0 and (t_min < 0.0 or t < t_min):
            hit_u = u
            hit_v = v
            t_min = t
            mat = int(triangles[i, 18])
            hit_type = 3
            hit_index = i

    if abs(rd_y) >= EPS:
        t = (plane_h - ro_y) / rd_y
        if t > 0.0 and (t_min < 0.0 or t < t_min):
            t_min = t
            mat = 0
            hit_type = 0
            hit_index = -1

    return t_min, mat, hit_type, hit_index, hit_u, hit_v


@cuda.jit(device=True)
def get_normal(hit_x, hit_y, hit_z, hit_type, hit_index, spheres, boxes, triangles, u, v):
    if hit_type == 0:
        return 0.0, 1.0, 0.0

    if hit_type == 1:
        nx = hit_x - spheres[hit_index, 0]
        ny = hit_y - spheres[hit_index, 1]
        nz = hit_z - spheres[hit_index, 2]
    
    elif hit_type == 3:
        n0x = triangles[hit_index, 9]
        n0y = triangles[hit_index, 10]
        n0z = triangles[hit_index, 11]

        n1x = triangles[hit_index, 12]
        n1y = triangles[hit_index, 13]
        n1z = triangles[hit_index, 14]

        n2x = triangles[hit_index, 15]
        n2y = triangles[hit_index, 16]
        n2z = triangles[hit_index, 17]

        w = 1.0 - u - v

        nx = n0x * w + n1x * u + n2x * v
        ny = n0y * w + n1y * u + n2y * v
        nz = n0z * w + n1z * u + n2z * v

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
def simple_shadow(hit_x, hit_y, hit_z,
                  nx, ny, nz,
                  lx, ly, lz,
                  spheres, boxes, triangles, plane_h):

    rd_x = lx
    rd_y = ly
    rd_z = lz

    dot_nl = nx * rd_x + ny * rd_y + nz * rd_z
    bias = HIT_BIAS if dot_nl > 0.0 else -HIT_BIAS

    ro_x = hit_x + nx * bias
    ro_y = hit_y + ny * bias
    ro_z = hit_z + nz * bias

    t, _, hit_type, _, _, _ = trace_scene(
        ro_x, ro_y, ro_z,
        rd_x, rd_y, rd_z,
        spheres, boxes, triangles, plane_h
    )

    if t < HIT_BIAS:
        return 1.0

    if hit_type == 0:
        return 1.0

    return 0.0


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
    bounces,  # игнорируем
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
    triangles,
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

    out_r = 0.0
    out_g = 0.0
    out_b = 0.0
    depth = 0.0

    for _ in range(samples):

        # --- generate ray ---
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

        # --- trace ---
        t, mat_id, hit_type, hit_index, u, v = trace_scene(
            ro_x, ro_y, ro_z,
            rd_x, rd_y, rd_z,
            spheres, boxes, triangles, plane_h
        )

        if t > 0.0:

            hit_x = ro_x + rd_x * t
            hit_y = ro_y + rd_y * t
            hit_z = ro_z + rd_z * t

            nx, ny, nz = get_normal(
                hit_x, hit_y, hit_z,
                hit_type, hit_index,
                spheres, boxes, triangles,
                u, v
            )

            lambert = (nx * lx + ny * ly + nz * lz)
            if lambert < 0.0:
                lambert = 0.0

            if lambert <= 0.0:
                visibility = 1.0
            else:
                visibility = simple_shadow(
                    hit_x, hit_y, hit_z,
                    nx, ny, nz,
                    lx, ly, lz,
                    spheres, boxes, triangles, plane_h
                )

            lighting = lambert * visibility

            base_r = materials[mat_id, 8]
            base_g = materials[mat_id, 9]
            base_b = materials[mat_id, 10]

            out_r += base_r * lighting
            out_g += base_g * lighting
            out_b += base_b * lighting
            depth += t

    inv = 1.0 / samples

    sample_rgb[y, x, 0] = out_r * inv
    sample_rgb[y, x, 1] = out_g * inv
    sample_rgb[y, x, 2] = out_b * inv
    sample_depth[y, x] = depth * inv

    sample_normal[y, x, 0] = 0.0
    sample_normal[y, x, 1] = 1.0
    sample_normal[y, x, 2] = 0.0
    sample_used[y, x] = 1.0


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
    lum = saturate01(lum + dither)
    # preserve shading while nudging structure with edge intensity
    lum = saturate01(lum + edge * 0.2)

    # decouple symbol mapping from color energy response
    symbol_lum = lum ** 0.85
    color_lum = lum ** 1.2

    r = saturate01(r)
    g = saturate01(g)
    b = saturate01(b)

    # normalize base color (chroma) independently from energy
    base_max = max(r, g, b, 1e-6)
    base_r = r / base_max
    base_g = g / base_max
    base_b = b / base_max

    # luminance-driven energy scaling for perceived depth/contrast
    energy = 0.2 + 0.8 * color_lum
    rgb_r = base_r * energy
    rgb_g = base_g * energy
    rgb_b = base_b * energy

    # optional compression to avoid oversaturation after scaling
    max_c = max(rgb_r, rgb_g, rgb_b)
    if max_c > 1.0:
        rgb_r /= max_c
        rgb_g /= max_c
        rgb_b /= max_c

    buffer_rgb[y, x, 0] = saturate01(rgb_r)
    buffer_rgb[y, x, 1] = saturate01(rgb_g)
    buffer_rgb[y, x, 2] = saturate01(rgb_b)
    luminance_buffer[y, x] = symbol_lum
    edge_buffer[y, x] = edge


def ascii_map(luminance_buffer, edge_buffer, chars):
    hist, bin_edges = np.histogram(
        luminance_buffer,
        bins=max(8, min(128, len(chars))),
        range=(0.0, 1.0)
    )

    cdf = np.cumsum(hist).astype(np.float32)

    if cdf[-1] > 0.0:
        cdf /= cdf[-1]
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        remapped = np.interp(
            luminance_buffer.ravel(),
            bin_centers,
            cdf
        ).reshape(luminance_buffer.shape)
    else:
        remapped = luminance_buffer

    char_scale = float(len(chars) - 1)
    idx = np.clip((remapped * char_scale).astype(np.int32), 0, len(chars) - 1)

    strong_edge_idx = int(0.88 * char_scale)
    idx = np.where(edge_buffer > 0.28, np.maximum(idx, strong_edge_idx), idx)

    return idx.astype(np.int32)


def render_frame_buffer(
    W, H, aspect,
    scene_data,
    camera_data,
    render_settings,
    lighting_settings,
    light_data,
    chars,
    state: RendererState
):

    # ---- unpack scene ----
    spheres = scene_data["spheres"]
    boxes = scene_data["boxes"]
    triangles = scene_data["triangles"]
    plane_y = scene_data["plane_y"]

    d_spheres = scene_data["d_spheres"]
    d_boxes = scene_data["d_boxes"]
    d_triangles = scene_data["d_triangles"]
    d_materials = scene_data["d_materials"]

    # ---- unpack camera ----
    ro = camera_data["ro"]
    forward = camera_data["forward"]
    right = camera_data["right"]
    up = camera_data["up"]

    # ---- light ----
    light = get_light(light_data)

    samples = int(render_settings["samples"])
    bounces = int(render_settings["bounces"])

    ambient_on = int(lighting_settings["ambient"])
    sky_on = int(lighting_settings["sky"])
    soft_shadow_on = int(lighting_settings["soft_shadows"])
    hard_shadow_on = int(lighting_settings["hard_shadows"])
    reflection_on = int(lighting_settings["reflections"])
    refraction_on = int(lighting_settings["refraction"])
    fresnel_on = int(lighting_settings.get("fresnel", 1))

    exposure = np.float32(render_settings.get("exposure", 1.0))
    gamma = np.float32(render_settings.get("gamma", 1.0))
    diffuse_gi_strength = np.float32(render_settings.get("diffuse_gi_strength", 0.25))

    # ---- change detection ----
    scene_changed = scene_data["changed"]
    camera_state = _camera_state(ro, forward, right, up)

    camera_changed = (
        state.prev_camera_state is None
        or not np.allclose(state.prev_camera_state, camera_state, atol=1e-6)
    )

    state.prev_camera_state = camera_state

    if state.accum_shape != (H, W):
        _reset_accumulation(state, W, H)
    elif scene_changed or camera_changed:
        _reset_accumulation(state, W, H)

    # ---- buffers ----
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

    # ---- RNG ----
    total_threads = W * H
    if state.rng_states is None or state.rng_size != total_threads:
        seed = np.random.randint(1, 1_000_000)
        state.rng_states = create_xoroshiro128p_states(total_threads, seed=seed)
        state.rng_size = total_threads

    rng_states = state.rng_states

    # ---- launch ----
    threads = (16, 16)
    blocks = ((W + 15) // 16, (H + 15) // 16)

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
        d_spheres,
        d_boxes,
        d_triangles,
        np.float32(plane_y),
        diffuse_gi_strength,
        d_materials,
        rng_states,
        state.accum_rgb,
        state.sample_count,
    )

    accumulate_kernel[blocks, threads](
        state.accum_rgb,
        state.sample_count,
        d_sample_rgb,
        d_sample_used
    )

    postprocess_kernel[blocks, threads](
        d_buffer_rgb,
        d_luminance,
        d_edge,
        state.accum_rgb,
        state.sample_count,
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

    return luminance_buffer, edge_buffer, buffer_rgb


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