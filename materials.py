import numpy as np


# rows: [diffuse, specular, shininess, reflectivity, roughness, refractivity], index == mat_id
MATERIALS = np.array(
    [
        [0.8, 0.10, 24.0, 0.05, 0.30, 0.00],  # plane
        [0.7, 0.35, 48.0, 0.35, 0.08, 0.00],  # sphere
        [0.6, 0.50, 64.0, 0.60, 0.02, 0.00],  # box
    ],
    dtype=np.float32,
)