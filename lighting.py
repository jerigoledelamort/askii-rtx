import math
from numba import njit

import config
from materials import MATERIALS


def get_light():
    light = config.LIGHT["direction"]
    l = math.sqrt(light[0] * light[0] + light[1] * light[1] + light[2] * light[2])
    return (light[0] / l, light[1] / l, light[2] / l)


@njit
def reflect(direction, normal):
    dot = direction[0] * normal[0] + direction[1] * normal[1] + direction[2] * normal[2]
    return (
        direction[0] - 2.0 * dot * normal[0],
        direction[1] - 2.0 * dot * normal[1],
        direction[2] - 2.0 * dot * normal[2],
    )


@njit
def local_lighting(rd, normal, light, mat_id, lambert, shadow, ambient_on):
    diffuse_strength = MATERIALS[mat_id, 0]
    specular_strength = MATERIALS[mat_id, 1]
    shininess = MATERIALS[mat_id, 2]

    ambient = 0.05 if ambient_on == 1 else 0.0
    diffuse = diffuse_strength * lambert * shadow

    view_dir = (-rd[0], -rd[1], -rd[2])
    light_reflect = reflect(light, normal)
    spec_angle = (
        view_dir[0] * light_reflect[0]
        + view_dir[1] * light_reflect[1]
        + view_dir[2] * light_reflect[2]
    )
    if spec_angle < 0.0:
        spec_angle = 0.0

    specular = specular_strength * (spec_angle ** shininess) * shadow
    return ambient + diffuse + specular