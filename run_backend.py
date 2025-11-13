#!/usr/bin/env python3

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

os.chdir(project_root)

print('starting openslam backend')
print(f'root: {project_root}')

import config

print(f'backend: http://{config.BACKEND_HOST}:{config.BACKEND_PORT}')
print(f'docs: http://{config.BACKEND_HOST}:{config.BACKEND_PORT}/docs')

import uvicorn
uvicorn.run('backend.api.main:app', host=config.BACKEND_HOST, port=config.BACKEND_PORT, reload=False, log_level=config.LOG_LEVEL.lower())
