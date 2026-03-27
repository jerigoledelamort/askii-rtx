import math
from tracer import trace
import config
from scene import get_scene

def get_light():
    light = config.LIGHT["direction"]
    l = math.sqrt(sum(i*i for i in light))
    return tuple(i/l for i in light)

def get_normal(p, mat, time):
    scene = get_scene(time)

    if mat == 1:  # sphere
        center = scene["sphere"]["pos"]
        n = (
            p[0] - center[0],
            p[1] - center[1],
            p[2] - center[2]
        )
        l = math.sqrt(sum(i*i for i in n))
        return tuple(i/l for i in n)

    if mat == 2:  # box
        center = scene["box"]["pos"]
        size = scene["box"]["size"]

        local = [p[i] - center[i] for i in range(3)]
        abs_local = [abs(local[i]) for i in range(3)]

        max_i = abs_local.index(max(abs_local))

        normal = [0, 0, 0]
        normal[max_i] = 1 if local[max_i] > 0 else -1
        return tuple(normal)
    
    if mat == 0:
        return (0, 1, 0)


def reflect(rd, n):
    dot = sum(rd[i]*n[i] for i in range(3))
    return tuple(rd[i] - 2*dot*n[i] for i in range(3))


def shadow(p, light, time):
    t, _ = trace(
        (p[0] + light[0]*0.01,
         p[1] + light[1]*0.01,
         p[2] + light[2]*0.01),
        light,
        time
    )
    return 0 if t is not None else 1


def shade(ro, rd, light, time):
    color = 0
    ro2 = ro
    rd2 = rd

    def get_material(mat_id):
        if mat_id == 0:
            return {"diff": 0.9, "spec": 0.0, "rough": 1.0}
        if mat_id == 1:
            return {"diff": 0.7, "spec": 0.3, "rough": 0.4}
        if mat_id == 2:
            return {"diff": 0.6, "spec": 0.6, "rough": 0.2}

    for bounce in range(config.RENDER["bounces"]):
        t, mat = trace(ro2, rd2, time)

        if t is None:
            break

        p = tuple(ro2[i] + rd2[i]*t for i in range(3))
        n = get_normal(p, mat, time)

        mat_data = get_material(mat)

        diff = max(sum(n[i]*light[i] for i in range(3)), 0)
        diff *= shadow(p, light, time)

        refl_light = reflect(tuple(-light[i] for i in range(3)), n)
        spec = max(sum(refl_light[i]*(-rd2[i]) for i in range(3)), 0)
        spec = spec ** (1.0 / mat_data["rough"])

        color += (
            diff * mat_data["diff"] +
            spec * mat_data["spec"]
        ) * (0.6 if bounce == 0 else 0.3)

        rd2 = reflect(rd2, n)
        ro2 = tuple(p[i] + n[i]*0.01 for i in range(3))

    return max(0, min(color, 1))