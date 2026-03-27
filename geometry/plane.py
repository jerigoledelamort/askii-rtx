def hit_plane(ro, rd, height):
    if abs(rd[1]) < 1e-6:
        return None

    t = (height - ro[1]) / rd[1]
    return t if t > 0 else None