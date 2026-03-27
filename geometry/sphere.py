import math

def hit_sphere(ro, rd, center, radius):
    oc = tuple(ro[i] - center[i] for i in range(3))

    a = sum(rd[i]*rd[i] for i in range(3))
    b = 2.0 * sum(oc[i]*rd[i] for i in range(3))
    c = sum(oc[i]*oc[i] for i in range(3)) - radius*radius

    disc = b*b - 4*a*c
    if disc < 0:
        return None

    t = (-b - math.sqrt(disc)) / (2*a)
    return t if t > 0 else None