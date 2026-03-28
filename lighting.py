import math
from numba import njit

import config
from materials import MATERIALS


def get_light():
    light = config.LIGHT["direction"]
    l = math.sqrt(light[0] * light[0] + light[1] * light[1] + light[2] * light[2])
    return (
        light[0] / l,
        light[1] / l,
        light[2] / l,
    )


@njit
def reflect_components(dx, dy, dz, nx, ny, nz):
    dot = dx * nx + dy * ny + dz * nz
    return (
        dx - 2.0 * dot * nx,
        dy - 2.0 * dot * ny,
        dz - 2.0 * dot * nz,
    )


@njit
def local_lighting(rd_x, rd_y, rd_z, nx, ny, nz, lx, ly, lz, mat_id, lambert, shadow, ambient_on):
    diffuse_strength = MATERIALS[mat_id, 0]
    specular_strength = MATERIALS[mat_id, 1]
    shininess = MATERIALS[mat_id, 2]

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