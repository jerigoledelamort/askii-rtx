import numpy as np


MATERIALS = np.array(
    [
        # diffuse, specular, shininess, reflectivity, roughness, refractivity,ior, absorption, r, g, b
        [0.95, 0.05, 8.0,   0.00, 0.65, 0.00, 1.00, 0.00, 0.95, 0.95, 0.95],  # 0 — matte
        [0.70, 0.30, 64.0,  0.20, 0.20, 0.00, 1.00, 0.00, 0.95, 0.45, 0.35],  # 1 — glossy plastic
        [0.70, 0.30, 32.0,  0.35, 0.25, 0.10, 1.20, 0.08, 0.35, 0.85, 0.45],  # 2 — mixed
        [0.05, 0.10, 96.0,  0.05, 0.04, 0.95, 1.50, 0.22, 0.90, 0.96, 1.00],  # 3 — glass
        [0.00, 1.00, 128.0, 1.00, 0.00, 0.00, 1.00, 0.00, 0.95, 0.95, 1.00],  # 4 — mirror
    ],
    dtype=np.float32,
)