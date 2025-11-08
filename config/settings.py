import os
from pathlib import Path

# Get the project root directory (OpenSLAM_v0.1)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Base directories
BASE_DIR = PROJECT_ROOT.parent
DATA_DIR = os.environ.get('OPENSLAM_DATA_DIR', os.path.join(BASE_DIR, "data"))
KITTI_DATASET_PATH = os.path.join(DATA_DIR, "00")

# Project directories
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
SHARED_DIR = os.path.join(PROJECT_ROOT, "shared")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# Runtime directories
LOG_DIR = os.environ.get('OPENSLAM_LOG_DIR', os.path.join(BASE_DIR, "logs"))
TEMP_DIR = os.environ.get('OPENSLAM_TEMP_DIR', os.path.join(BASE_DIR, "temp"))

# Create directories if they don't exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)