import numpy as np


# rows: [diffuse, specular, roughness], index == mat_id
MATERIALS = np.array(
    [
        [0.8, 0.0, 1.0],  # plane
        [0.7, 0.3, 0.3],  # sphere
        [0.6, 0.6, 0.1],  # box
    ],
    dtype=np.float32,
)