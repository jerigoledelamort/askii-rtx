from scene import get_scene

from geometry.sphere import hit_sphere
from geometry.box import hit_box
from geometry.plane import hit_plane

def trace(ro, rd, time):
    scene = get_scene(time)

    s = scene["sphere"]
    b = scene["box"]
    pl = scene["plane"]

    t_min = None
    mat = None

    t = hit_sphere(ro, rd, tuple(s["pos"]), s["radius"])
    if t is not None:
        t_min = t
        mat = 1

    t = hit_box(ro, rd, tuple(b["pos"]), tuple(b["size"]))
    if t is not None and (t_min is None or t < t_min):
        t_min = t
        mat = 2

    t = hit_plane(ro, rd, pl["height"])
    if t is not None and (t_min is None or t < t_min):
        t_min = t
        mat = 0

    return t_min, mat