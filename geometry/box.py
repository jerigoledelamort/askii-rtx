from numba import njit


@njit
def hit_box(ro, rd, cx, cy, cz, sx, sy, sz):
    min_x = cx - sx
    min_y = cy - sy
    min_z = cz - sz
    max_x = cx + sx
    max_y = cy + sy
    max_z = cz + sz

    tmin = -1e9
    tmax = 1e9

    if abs(rd[0]) < 1e-6:
        if ro[0] < min_x or ro[0] > max_x:
            return -1.0
    else:
        t1 = (min_x - ro[0]) / rd[0]
        t2 = (max_x - ro[0]) / rd[0]
        lo = t1 if t1 < t2 else t2
        hi = t2 if t2 > t1 else t1
        tmin = lo if lo > tmin else tmin
        tmax = hi if hi < tmax else tmax
        if tmax < tmin:
            return -1.0

    if abs(rd[1]) < 1e-6:
        if ro[1] < min_y or ro[1] > max_y:
            return -1.0
    else:
        t1 = (min_y - ro[1]) / rd[1]
        t2 = (max_y - ro[1]) / rd[1]
        lo = t1 if t1 < t2 else t2
        hi = t2 if t2 > t1 else t1
        tmin = lo if lo > tmin else tmin
        tmax = hi if hi < tmax else tmax
        if tmax < tmin:
            return -1.0

    if abs(rd[2]) < 1e-6:
        if ro[2] < min_z or ro[2] > max_z:
            return -1.0
    else:
        t1 = (min_z - ro[2]) / rd[2]
        t2 = (max_z - ro[2]) / rd[2]
        lo = t1 if t1 < t2 else t2
        hi = t2 if t2 > t1 else t1
        tmin = lo if lo > tmin else tmin
        tmax = hi if hi < tmax else tmax
        if tmax < tmin:
            return -1.0

    if tmin > 0.0:
        return tmin
    return tmax if tmax > 0.0 else -1.0