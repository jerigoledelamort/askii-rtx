from numba import njit

from geometry.sphere import hit_sphere
from geometry.box import hit_box
from geometry.plane import hit_plane


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