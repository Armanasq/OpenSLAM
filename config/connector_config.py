CONNECTOR_DIR = 'connectors'

CONNECTOR_TYPES = ['transform', 'parser', 'generator', 'validator']

BUILTIN_TRANSFORMS = {
    'identity': 'pass through unchanged',
    'quaternion_to_matrix': 'convert quaternion to rotation matrix',
    'matrix_to_quaternion': 'convert rotation matrix to quaternion',
    'tum_to_kitti': 'convert TUM format to KITTI format',
    'kitti_to_tum': 'convert KITTI format to TUM format',
    'extract_positions': 'extract xyz positions from poses',
    'extract_rotations': 'extract rotation matrices from poses'
}

BUILTIN_PARSERS = {
    'tum_trajectory': 'timestamp tx ty tz qx qy qz qw',
    'kitti_trajectory': '12 values per line as 3x4 matrix',
    'euroc_trajectory': 'csv with timestamp and pose',
    'json_trajectory': 'json array of poses',
    'numpy_array': 'numpy npy or npz file'
}

BUILTIN_GENERATORS = {
    'image_list': 'generate list of image paths from directory',
    'calibration_yaml': 'generate calibration yaml from parameters',
    'settings_file': 'generate settings file from template',
    'vocabulary_download': 'download vocabulary file from url'
}

VARIABLE_PATTERN = r'\$\{([^}]+)\}'
PATH_PATTERN = r'([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'

MOUNT_MODE_RO = 'ro'
MOUNT_MODE_RW = 'rw'
