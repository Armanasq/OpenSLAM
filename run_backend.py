#!/usr/bin/env python3

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

os.chdir(project_root)

# Read configuration from environment variables
BACKEND_HOST = os.getenv('OPENSLAM_BACKEND_HOST', '0.0.0.0')
BACKEND_PORT = int(os.getenv('OPENSLAM_BACKEND_PORT', 8007))
LOG_LEVEL = os.getenv('OPENSLAM_LOG_LEVEL', 'INFO')

print('starting openslam backend')
print(f'root: {project_root}')
print(f'backend: http://{BACKEND_HOST}:{BACKEND_PORT}')
print(f'docs: http://{BACKEND_HOST}:{BACKEND_PORT}/docs')

import uvicorn
uvicorn.run('backend.api.main:app', host=BACKEND_HOST, port=BACKEND_PORT, reload=False, log_level=LOG_LEVEL.lower())
