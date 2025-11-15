import os
from pathlib import Path
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results'
CACHE_DIR = BASE_DIR / 'cache'
PLOT_DIR = BASE_DIR / 'plots'
TEMP_DIR = BASE_DIR / 'temp'
ALIGNMENT_METHODS = ['se3', 'sim3', 'yaw_only', 'auto']
DEFAULT_ALIGNMENT = 'sim3'
RPE_DELTA_VALUES = [1.0, 5.0, 10.0]
RPE_DELTA_UNIT = 'meters'
FAILURE_THRESHOLD = 2.0
COMPLETION_THRESHOLD = 0.95
PLOT_DPI = 300
PLOT_FORMATS = ['png', 'pdf']
PLOT_STYLE = 'seaborn-v0_8-whitegrid'
FIGURE_SIZE_2D = (12, 10)
FIGURE_SIZE_3D = (14, 10)
FIGURE_SIZE_ERROR = (12, 6)
DATASET_FORMATS = {
    'kitti': {'extensions': ['.txt'], 'has_timestamps': True, 'pose_format': 'matrix_3x4'},
    'euroc': {'extensions': ['.csv'], 'has_timestamps': True, 'pose_format': 'xyz_quat'},
    'tum': {'extensions': ['.txt'], 'has_timestamps': True, 'pose_format': 'xyz_quat'},
    'rosbag': {'extensions': ['.bag'], 'has_timestamps': True, 'pose_format': 'ros_msg'},
    'custom': {'extensions': ['.txt', '.csv'], 'has_timestamps': True, 'pose_format': 'auto'}
}
METRICS_CONFIG = {
    'ate': {'enabled': True, 'alignment': 'auto'},
    'rpe': {'enabled': True, 'delta': RPE_DELTA_VALUES, 'unit': RPE_DELTA_UNIT},
    'robustness': {'enabled': True, 'threshold': FAILURE_THRESHOLD},
    'completion': {'enabled': True, 'threshold': COMPLETION_THRESHOLD}
}
MOTION_CATEGORIES = ['forward', 'backward', 'left', 'right', 'rotation_cw', 'rotation_ccw', 'stationary']
VELOCITY_THRESHOLD = 0.1
ANGULAR_VELOCITY_THRESHOLD = 0.05
OUTPUT_FORMATS = ['json', 'csv', 'latex', 'markdown']
LATEX_STYLES = ['ieee', 'neurips', 'icra', 'cvpr', 'plain']
PARALLEL_WORKERS = os.cpu_count()
LOG_LEVEL = 'INFO'
PRECISION_DECIMALS = 4
for d in [DATA_DIR, RESULTS_DIR, CACHE_DIR, PLOT_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)
