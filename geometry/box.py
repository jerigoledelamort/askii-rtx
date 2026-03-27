def hit_box(ro, rd, center, size):
    min_b = [center[i] - size[i] for i in range(3)]
    max_b = [center[i] + size[i] for i in range(3)]

    tmin = -1e9
    tmax = 1e9

    for i in range(3):
        if abs(rd[i]) < 1e-6:
            if ro[i] < min_b[i] or ro[i] > max_b[i]:
                return None
        else:
            t1 = (min_b[i] - ro[i]) / rd[i]
            t2 = (max_b[i] - ro[i]) / rd[i]

            tmin = max(tmin, min(t1, t2))
            tmax = min(tmax, max(t1, t2))

            if tmax < tmin:
                return None

    return tmin if tmin > 0 else tmax