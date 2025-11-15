import os
from pathlib import Path

# BASE_DIR is the OpenSLAM root directory (parent of config/ directory)
BASE_DIR = Path(__file__).parent.parent.absolute()

DATA_DIR = os.getenv('OPENSLAM_DATA_DIR', BASE_DIR / 'data')
LOG_DIR = os.getenv('OPENSLAM_LOG_DIR', BASE_DIR / 'logs')
TEMP_DIR = os.getenv('OPENSLAM_TEMP_DIR', BASE_DIR / 'temp')
UPLOAD_DIR = BASE_DIR / 'uploads'
RESULTS_DIR = BASE_DIR / 'results'
CACHE_DIR = BASE_DIR / 'cache'

BACKEND_HOST = os.getenv('OPENSLAM_BACKEND_HOST', '0.0.0.0')
BACKEND_PORT = int(os.getenv('OPENSLAM_BACKEND_PORT', 8007))
FRONTEND_PORT = int(os.getenv('OPENSLAM_FRONTEND_PORT', 3001))

MAX_UPLOAD_SIZE = 10 * 1024 * 1024 * 1024
CHUNK_SIZE = 8192
MAX_WORKERS = int(os.getenv('OPENSLAM_MAX_WORKERS', os.cpu_count() or 4))

DATASET_FORMATS = {
    'kitti': {
        'required': ['sequences', 'calib.txt'],
        'optional': ['times.txt', 'poses']
    },
    'euroc': {
        'required': ['mav0'],
        'optional': ['cam0', 'cam1', 'imu0']
    },
    'tum': {
        'required': ['rgb.txt', 'depth.txt'],
        'optional': ['groundtruth.txt', 'accelerometer.txt']
    },
    'rosbag': {
        'required': ['.bag'],
        'optional': []
    },
    'custom': {
        'required': [],
        'optional': []
    }
}

SENSOR_TYPES = ['camera', 'stereo', 'rgbd', 'lidar', 'imu', 'gps', 'event']

ALGORITHM_INTERFACE_METHODS = ['initialize', 'process_frame', 'finalize']

ALIGNMENT_METHODS = ['se3', 'sim3', 'yaw_only', 'auto']
DEFAULT_ALIGNMENT = 'auto'

METRICS = {
    'ate': {'name': 'Absolute Trajectory Error', 'unit': 'm'},
    'rpe': {'name': 'Relative Pose Error', 'unit': 'm'},
    'rpe_trans': {'name': 'RPE Translation', 'unit': 'm'},
    'rpe_rot': {'name': 'RPE Rotation', 'unit': 'deg'},
    'success_rate': {'name': 'Success Rate', 'unit': '%'},
    'runtime': {'name': 'Runtime', 'unit': 's'},
    'fps': {'name': 'Frames Per Second', 'unit': 'Hz'}
}

PLOT_TYPES = ['trajectory_2d', 'trajectory_3d', 'error_time', 'error_dist', 'comparison_box', 'comparison_radar']
PLOT_FORMATS = ['png', 'pdf', 'svg', 'html', 'latex']
PLOT_DPI = 300
PLOT_STYLE = 'seaborn-v0_8-darkgrid'

VIZ_UPDATE_RATE = 30
VIZ_BUFFER_SIZE = 1000
VIZ_POINT_CLOUD_SUBSAMPLE = 10

FAILURE_RISK_THRESHOLD = 0.75
FAILURE_PREDICTION_WINDOW = 5.0

TASK_TYPES = ['navigation', 'manipulation', 'inspection', 'custom']
TASK_REQUIREMENTS = {
    'navigation': {'accuracy': 0.1, 'precision': 0.05, 'update_rate': 10, 'robustness': 0.95},
    'manipulation': {'accuracy': 0.05, 'precision': 0.02, 'update_rate': 30, 'robustness': 0.98},
    'inspection': {'accuracy': 0.02, 'precision': 0.01, 'update_rate': 5, 'robustness': 0.90}
}

MULTI_RUN_DEFAULT = 10
CONFIDENCE_LEVEL = 0.95
SIGNIFICANCE_LEVEL = 0.05

PARAM_SWEEP_STRATEGIES = ['grid', 'random', 'bayesian']
PARAM_SWEEP_DEFAULT_SAMPLES = 50

DOCKER_REGISTRY = os.getenv('OPENSLAM_DOCKER_REGISTRY', 'openslam')
DOCKER_BASE_IMAGE = f'{DOCKER_REGISTRY}/base:latest'

POPULAR_ALGORITHMS = ['orb_slam3', 'vins_mono', 'vins_fusion', 'lio_sam', 'rtabmap', 'cartographer', 'loam', 'dso', 'svo']

WS_HEARTBEAT_INTERVAL = 30
WS_MAX_MESSAGE_SIZE = 10 * 1024 * 1024

LOG_LEVEL = os.getenv('OPENSLAM_LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

DB_TYPE = os.getenv('OPENSLAM_DB_TYPE', 'sqlite')
DB_PATH = os.getenv('OPENSLAM_DB_PATH', str(BASE_DIR / 'openslam.db'))
DB_POOL_SIZE = 10

CACHE_ENABLED = os.getenv('OPENSLAM_CACHE_ENABLED', 'true').lower() == 'true'
CACHE_TTL = 3600

# Create required directories
for d in [DATA_DIR, LOG_DIR, TEMP_DIR, UPLOAD_DIR, RESULTS_DIR, CACHE_DIR]:
    Path(d).mkdir(parents=True, exist_ok=True)
