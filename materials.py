import numpy as np


MATERIALS = np.array(
    [
        # diffuse, specular, shininess, reflectivity, roughness, refractivity

        [0.9, 0.05, 8.0,   0.0, 0.6, 0.0],   # 0 — матовый
        [0.6, 0.4,  64.0,  0.1, 0.1, 0.0],   # 1 — глянцевый
        [0.7, 0.3,  32.0,  0.3, 0.2, 0.0],   # 2 — смесь
        [0.1, 0.1,  64.0,  0.1, 0.0, 0.9],   # 3 — стекло
        [0.0, 1.0,  128.0, 1.0, 0.0, 0.0],   # 4 — зеркало
    ],
    dtype=np.float32,
)