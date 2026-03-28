from numba import njit


@njit
def hit_plane(ro, rd, height):
    if abs(rd[1]) < 1e-6:
        return -1.0

    t = (height - ro[1]) / rd[1]
    return t if t > 0.0 else -1.0