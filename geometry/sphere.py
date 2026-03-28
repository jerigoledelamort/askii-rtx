import math
from numba import njit


@njit
def hit_sphere(ro, rd, cx, cy, cz, radius):
    ocx = ro[0] - cx
    ocy = ro[1] - cy
    ocz = ro[2] - cz

    a = rd[0] * rd[0] + rd[1] * rd[1] + rd[2] * rd[2]
    b = 2.0 * (ocx * rd[0] + ocy * rd[1] + ocz * rd[2])
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