# OpenSLAM - Accurate Design Document

## Overview

OpenSLAM is a zero-copy SLAM evaluation platform with FastAPI backend and React frontend. Architecture is **monolithic** with modular utility functions, using in-memory storage and WebSocket for real-time updates.

## Actual Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Frontend (React 18, Port 3001)               │
│                                                               │
│  App.js (Monolithic Component)                               │
│  ├─ Datasets View (inline)                                   │
│  ├─ Algorithms View (inline)                                 │
│  ├─ Runs View (inline)                                       │
│  └─ Results View (inline)                                    │
│                                                               │
│  WebSocket Client + Fetch API (inline)                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                    REST + WebSocket
                         │
┌────────────────────────┼─────────────────────────────────────┐
│              Backend (FastAPI, Port 8007)                     │
│                                                               │
│  backend/api/main.py (~580 lines, ALL routes)                │
│  ├─ POST /api/dataset/load                                   │
│  ├─ POST /api/upload                                         │
│  ├─ GET /api/datasets                                        │
│  ├─ GET /api/dataset/{id}                                    │
│  ├─ GET /api/dataset/{id}/preview                            │
│  ├─ GET /api/dataset/{id}/frame/{index}                      │
│  ├─ POST /api/dataset/{id}/process                           │
│  ├─ DELETE /api/dataset/{id}                                 │
│  ├─ POST /api/algorithm                                      │
│  ├─ GET /api/algorithms                                      │
│  ├─ POST /api/run                                            │
│  ├─ GET /api/runs                                            │
│  ├─ GET /api/health                                          │
│  ├─ WS /ws/{client_id}                                       │
│  └─ ... (~30 endpoints total)                                │
│                                                               │
│  In-Memory Storage (module-level dicts)                      │
│  ├─ datasets = {}                                            │
│  ├─ algorithms = {}                                          │
│  ├─ runs = {}                                                │
│  ├─ comparisons = {}                                         │
│  └─ ws_connections = {}                                      │
│                                                               │
│  Helper Functions (inline in main.py)                        │
│  ├─ _get_dataset_frames(path, format, max_frames)           │
│  ├─ _get_dir_size(path)                                     │
│  ├─ _log_activity(action, resource_type, resource_id)       │
│  └─ _broadcast_update(event)                                │
└────────────────────────┬─────────────────────────────────────┘
                         │
                    Imports Utilities
                         │
┌────────────────────────┼─────────────────────────────────────┐
│                   core/ (29 utility modules)                  │
│                                                               │
│  Format Detection & Data Loading:                            │
│  ├─ format_detector.py (detect_format, get_dataset_structure)│
│  ├─ format_converter.py (convert between formats)            │
│  ├─ data_loader.py (DataLoader class for frame loading)      │
│  └─ dataset_loader.py (detect_format, load functions)        │
│                                                               │
│  Algorithm Integration:                                      │
│  ├─ connector_engine.py (ConnectorEngine class)              │
│  ├─ plugin_manager.py (plugin discovery, validation)         │
│  ├─ plugin_executor.py (PluginExecutor class)                │
│  ├─ algorithm_interface.py (interface definitions)           │
│  ├─ algorithm_registry.py (AlgorithmRegistry class)          │
│  └─ slam_interface.py (SLAM interface)                       │
│                                                               │
│  Execution & Orchestration:                                  │
│  ├─ docker_orchestrator.py (DockerOrchestrator class)        │
│  ├─ workflow_executor.py (WorkflowExecutor class)            │
│  └─ code_executor.py (code execution utilities)              │
│                                                               │
│  Trajectory & Metrics:                                       │
│  ├─ trajectory.py (trajectory processing functions)          │
│  ├─ alignment.py (align_trajectories functions)              │
│  ├─ gt_aligner.py (ground truth alignment)                   │
│  ├─ metrics.py (compute_ate, compute_rpe, etc.)              │
│  ├─ motion_analysis.py (motion analysis functions)           │
│  ├─ scene_analysis.py (complexity analysis)                  │
│  └─ task_metrics.py (task-specific metrics)                  │
│                                                               │
│  Visualization & Export:                                     │
│  ├─ visualization.py (plotting functions)                    │
│  ├─ visualizer.py (Visualizer class)                         │
│  ├─ plotter.py (trajectory plotting)                         │
│  └─ export.py (export to JSON, CSV, HDF5, LaTeX)             │
│                                                               │
│  Analysis & Utilities:                                       │
│  ├─ performance_analyzer.py (performance analysis)           │
│  ├─ performance_comparison.py (comparison utilities)         │
│  ├─ batch.py (batch processing)                              │
│  ├─ data_stream.py (data streaming)                          │
│  ├─ debugger.py (debugging utilities)                        │
│  └─ tutorial_manager.py (tutorial system)                    │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

**Backend:**
- FastAPI 0.104+ (async REST API)
- Python 3.10+
- Uvicorn (ASGI server)
- NumPy (trajectory computation)
- OpenCV (image processing)
- PyYAML (config parsing)
- WebSockets (real-time)
- Docker Python SDK (container orchestration)

**Frontend:**
- React 18.2.0
- react-scripts 5.0.1
- @craco/craco 7.1.0 (config override)
- Plotly.js 2.35.3 (visualization)
- react-router-dom 6.0.0 (routing)
- Native WebSocket API (real-time)
- Native Fetch API (HTTP)

**Infrastructure:**
- Node.js 18+ (frontend build)
- npm (package management)
- Bash (startup scripts)
- Git (version control)

## File Structure (Actual)

```
OpenSLAM/
├── backend/
│   ├── api/
│   │   └── main.py                    # ALL routes, WebSocket, in-memory storage (580 lines)
│   └── core/                          # 29 utility modules (functions and classes)
│       ├── algorithm_interface.py
│       ├── algorithm_registry.py
│       ├── alignment.py
│       ├── batch.py
│       ├── code_executor.py
│       ├── connector_engine.py
│       ├── data_loader.py
│       ├── data_stream.py
│       ├── dataset_loader.py
│       ├── debugger.py
│       ├── docker_orchestrator.py
│       ├── export.py
│       ├── format_converter.py
│       ├── format_detector.py
│       ├── gt_aligner.py
│       ├── metrics.py
│       ├── motion_analysis.py
│       ├── performance_analyzer.py
│       ├── performance_comparison.py
│       ├── plotter.py
│       ├── plugin_executor.py
│       ├── plugin_manager.py
│       ├── scene_analysis.py
│       ├── slam_interface.py
│       ├── task_metrics.py
│       ├── trajectory.py
│       ├── tutorial_manager.py
│       ├── visualization.py
│       ├── visualizer.py
│       └── workflow_executor.py
│
├── frontend/
│   ├── src/
│   │   ├── App.js                     # Monolithic component with all views (500+ lines)
│   │   ├── App.css                    # All styles (400+ lines)
│   │   ├── index.js                   # Entry point
│   │   ├── index.css                  # Base styles
│   │   ├── components/                # Limited separate components
│   │   └── config/                    # Frontend config constants
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   ├── craco.config.js               # Webpack/dev-server config override
│   └── tsconfig.json
│
├── config/
│   ├── __init__.py                    # ALL configuration (BASE_DIR, DATASET_FORMATS, METRICS, etc.)
│   ├── openslam_config.py            # OpenSLAM-specific config
│   ├── plugin_config.py              # Plugin system config
│   ├── connector_config.py           # Connector config
│   ├── docker_config.py              # Docker config
│   ├── cpp_plugin_config.py          # C++ plugin config
│   └── *.json                        # JSON config files
│
├── core/                              # Shared core modules (19 files)
│   ├── alignment.py
│   ├── batch.py
│   ├── connector_engine.py
│   ├── dataset_loader.py
│   ├── docker_orchestrator.py
│   ├── export.py
│   ├── format_converter.py
│   ├── metrics.py
│   ├── motion_analysis.py
│   ├── plugin_executor.py
│   ├── plugin_manager.py
│   ├── scene_analysis.py
│   ├── task_metrics.py
│   ├── trajectory.py
│   ├── visualization.py
│   └── workflow_executor.py
│
├── algorithms/                        # Pre-integrated SLAM algorithms
├── plugins/                           # Plugin directory
├── connectors/                        # Connector definitions (YAML)
├── data/                              # Dataset storage (zero-copy, path refs only)
├── uploads/                           # Uploaded file storage
├── results/                           # Evaluation results
├── cache/                             # Cache directory
├── temp/                              # Temporary files
├── logs/                              # Log files
├── plots/                             # Generated plots
├── docs/                              # Documentation (15 MD files)
├── examples/                          # Example configs (4 YAML files)
├── scripts/                           # Shell scripts (5 files)
├── tests/                             # Test files (3 files)
├── assets/                            # Images (logo.jpg)
├── others/                            # Archived/backup code
│
├── config.py.backup                   # Old config (backed up)
├── run_backend.py                     # Backend launcher
├── openslam.py                        # CLI tool
├── start_openslam.sh                  # Unified startup script
├── requirements.txt                   # Python dependencies
├── docker-compose.yml                 # Docker config
├── .gitignore
├── LICENSE
└── README.md
```

## Data Models (Actual Implementation)

### In-Memory Storage (backend/api/main.py)

```python
datasets = {}        # dict[str, dict]
algorithms = {}      # dict[str, dict]
runs = {}           # dict[str, dict]
comparisons = {}    # dict[str, dict]
tasks = {}          # dict[str, dict]
failures = {}       # dict[str, dict]
ws_connections = {} # dict[str, dict]
activity_log = []   # list[dict]
system_config = {}  # dict
```

### Dataset Object (dict, not class)

```python
dataset = {
    'id': str,                    # 8-char UUID
    'name': str,
    'description': str,
    'tags': list,
    'path': str,                  # Original dataset path (ZERO-COPY)
    'format': str,                # 'kitti', 'euroc', 'tum', 'rosbag', 'custom'
    'structure': {
        'path': str,
        'files': list,
        'dirs': list,
        'sensors': list,
        'frames': int,
        'duration': float,
        'has_gt': bool,
        'format': str
    },
    'valid': bool,
    'errors': list,
    'status': str,                # 'uploaded', 'processing', 'processed', 'failed'
    'created': str,               # ISO timestamp
    'updated': str,               # ISO timestamp
    'frames': int,
    'sequences': int,
    'size': str,                  # Human-readable (e.g., "2.6 MB")
    'file_count': int,
    'checksum': str,
    'metadata': dict,
    'sensors': list,
    'ground_truth': bool,
    'processed_path': str | None,
    'preview': {                  # IMMEDIATE preview, no processing needed
        'frames': list,           # List of absolute file paths
        'count': int,
        'urls': list              # List of API URLs
    } | None,
    'statistics': dict
}
```

### Algorithm Object (dict, not class)

```python
algorithm = {
    'id': str,                    # 8-char UUID
    'name': str,
    'description': str,
    'code': str,                  # Algorithm code (for custom algorithms)
    'params': dict,
    'template': str,              # 'custom', 'orb_slam3', 'vins_mono', etc.
    'tags': list,
    'type': str,                  # 'custom', 'plugin', 'connector'
    'created': str,               # ISO timestamp
    'updated': str,               # ISO timestamp
    'runs_count': int,
    'avg_ate': float | None,
    'avg_rpe': float | None,
    'success_rate': float | None,
    'last_run': str | None
}
```

### Run/Execution Object (dict, not class)

```python
run = {
    'id': str,                    # 8-char UUID
    'dataset_id': str,
    'algorithm_id': str,
    'dataset_name': str,
    'algorithm_name': str,
    'status': str,                # 'pending', 'running', 'completed', 'failed', 'cancelled'
    'created': str,               # ISO timestamp
    'started': str | None,        # ISO timestamp
    'completed': str | None,      # ISO timestamp
    'duration': float,            # seconds
    'progress': float,            # 0-100
    'current_frame': int,
    'total_frames': int,
    'config': dict,
    'result': {
        'trajectory': list | None,
        'metrics': dict | None,
        'output_path': str | None
    } | None,
    'error': {
        'code': str,
        'message': str,
        'stderr': str
    } | None
}
```

### Trajectory Format

```python
# NumPy array of 4x4 homogeneous transformation matrices
trajectory = np.ndarray(shape=(N, 4, 4), dtype=np.float64)

# Each matrix:
# [[r11, r12, r13, tx],
#  [r21, r22, r23, ty],
#  [r31, r32, r33, tz],
#  [0,   0,   0,   1 ]]
```

## Core Components (Actual Implementation)

### 1. Backend API (backend/api/main.py)

**Monolithic file with all functionality:**

#### Imports
```python
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import json, shutil, asyncio, numpy as np, sys, uuid, time, hashlib, re, os
```

#### App Initialization
```python
app = FastAPI(title='openslam', version='2.0.0', description='research-grade slam evaluation platform')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
```

#### Storage
```python
datasets = {}
algorithms = {}
runs = {}
comparisons = {}
tasks = {}
failures = {}
ws_connections = {}
activity_log = []
system_config = {'auto_process': False, 'max_concurrent_runs': 3, ...}
```

#### Helper Functions (inline)
```python
def _log_activity(action: str, resource_type: str, resource_id: str, details: Dict[str, Any] = None)
async def _broadcast_update(event: dict)
def _get_dir_size(path: Path) -> str
def _compute_dataset_statistics(ds: dict) -> dict
def _compute_comparison_statistics(runs_list: List[dict]) -> dict
def _compute_rankings(runs_list: List[dict]) -> List[dict]
def _get_dataset_frames(dataset_path: Path, dataset_format: str, max_frames: int = 5) -> list
```

#### Dataset Endpoints
```python
@app.post('/api/dataset/load')
async def load_dataset(data: dict = Body(...))
    # Validates path, detects format, scans structure
    # Generates preview IMMEDIATELY without copying files
    # Returns dataset object with preview URLs

@app.post('/api/upload')
async def upload(file: UploadFile = File(...))
    # Handles file uploads (zip, tar.gz)
    # Extracts and creates dataset

@app.get('/api/datasets')
def list_datasets(format, tag, search, sort, order, limit, offset)
    # Returns filtered/sorted/paginated dataset list

@app.get('/api/dataset/{dataset_id}')
def get_dataset(dataset_id: str)
    # Returns single dataset

@app.get('/api/dataset/{dataset_id}/preview')
async def get_dataset_preview(dataset_id: str, frame: Optional[int] = Query(0))
    # Returns preview metadata with frame URLs
    # NO processing required, works immediately after load

@app.get('/api/dataset/{dataset_id}/frame/{frame_index}')
async def get_dataset_frame(dataset_id: str, frame_index: int)
    # Serves frame image directly from dataset path (ZERO-COPY)
    # Returns FileResponse with image/png

@app.post('/api/dataset/{dataset_id}/process')
async def process_dataset(dataset_id: str)
    # Background processing (optional)

@app.delete('/api/dataset/{dataset_id}')
async def delete_dataset(dataset_id: str)
    # Removes from registry (does NOT delete files)
```

#### Algorithm Endpoints
```python
@app.post('/api/algorithm')
async def create_algorithm(data: dict = Body(...))
    # Creates custom algorithm

@app.get('/api/algorithms')
def list_algorithms(type, tag, search, sort, order)
    # Returns filtered/sorted algorithm list

@app.get('/api/algorithm/{algorithm_id}')
def get_algorithm(algorithm_id: str)
    # Returns single algorithm

@app.delete('/api/algorithm/{algorithm_id}')
async def delete_algorithm(algorithm_id: str)
    # Removes from registry
```

#### Execution Endpoints
```python
@app.post('/api/run')
async def create_run(data: dict = Body(...))
    # Creates and starts execution
    # Spawns background task

@app.get('/api/runs')
def list_runs(status, dataset_id, algorithm_id, sort, order, limit, offset)
    # Returns filtered/sorted/paginated run list

@app.get('/api/run/{run_id}')
def get_run(run_id: str)
    # Returns single run with progress

@app.delete('/api/run/{run_id}')
async def cancel_run(run_id: str)
    # Cancels or removes run
```

#### WebSocket
```python
@app.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: str)
    # Handles WebSocket connections
    # Broadcasts events: dataset_created, algorithm_created, run_updated, etc.
```

#### Health & Utility
```python
@app.get('/')
def root()
    # Returns basic info

@app.get('/api/health')
def health_check()
    # Returns status, counts, timestamp

@app.on_event('startup')
async def startup()
    # Creates directories
    # Prints startup banner

@app.on_event('shutdown')
async def shutdown()
    # Closes WebSocket connections
```

### 2. Configuration (config/__init__.py)

**Location:** Project root, NOT in backend/

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()  # OpenSLAM root

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
    'kitti': {'required': ['sequences', 'calib.txt'], 'optional': ['times.txt', 'poses']},
    'euroc': {'required': ['mav0'], 'optional': ['cam0', 'cam1', 'imu0']},
    'tum': {'required': ['rgb.txt', 'depth.txt'], 'optional': ['groundtruth.txt', 'accelerometer.txt']},
    'rosbag': {'required': ['.bag'], 'optional': []},
    'custom': {'required': [], 'optional': []}
}

SENSOR_TYPES = ['camera', 'stereo', 'rgbd', 'lidar', 'imu', 'gps', 'event']

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

# ... more config constants

for d in [DATA_DIR, LOG_DIR, TEMP_DIR, UPLOAD_DIR, RESULTS_DIR, CACHE_DIR]:
    Path(d).mkdir(parents=True, exist_ok=True)
```

### 3. Core Utility Modules (backend/core/ and core/)

**All modules use:**
```python
from config import openslam_config as cfg
from config import plugin_config as pcfg
from config import connector_config as ccfg
from config import docker_config as dcfg
```

#### format_detector.py
```python
def detect_format(path: Path) -> str
    # Checks for KITTI, EuRoC, TUM, ROS bag markers
    # Returns format string or 'custom'

def get_dataset_structure(path: Path) -> dict
    # Scans directory for files, dirs, sensors
    # Returns structure dict

def validate_dataset(path: Path, fmt: str = None) -> tuple[bool, list]
    # Validates required files exist
    # Returns (valid, errors)
```

#### connector_engine.py
```python
class ConnectorEngine:
    def __init__(self)
    def load_connector(self, path: str) -> dict
    def execute(self, connector: dict, dataset: dict, output_dir: Path) -> dict
    def _resolve_templates(self, template: str, context: dict) -> str
    def _execute_subprocess(self, command: list, env: dict, cwd: Path) -> tuple
```

#### plugin_manager.py
```python
def discover_plugins(plugin_dir: Path) -> list
def load_plugin(plugin_path: Path) -> dict
def validate_plugin(config: dict) -> bool
def get_plugin_function(plugin: dict, func_name: str)
```

#### docker_orchestrator.py
```python
class DockerOrchestrator:
    def __init__(self)
    def build_image(self, dockerfile_path: Path, tag: str) -> str
    def run_container(self, image: str, volumes: dict, env: dict, command: str) -> dict
    def monitor_container(self, container_id: str, callback) -> None
    def cleanup(self, container_id: str) -> None
```

#### metrics.py
```python
def compute_ate(estimated_poses: np.ndarray, ground_truth_poses: np.ndarray) -> dict
def compute_rpe(estimated_poses: np.ndarray, ground_truth_poses: np.ndarray, delta: float) -> dict
def compute_robustness(ate: dict, failures: list, completion: float) -> float
def detect_failures(errors: np.ndarray, threshold: float) -> list
def compute_statistics(errors: np.ndarray) -> dict
```

#### alignment.py
```python
def align_trajectories(estimated: np.ndarray, ground_truth: np.ndarray, method: str) -> tuple
def _horn(est: np.ndarray, gt: np.ndarray) -> tuple
def _umeyama(est: np.ndarray, gt: np.ndarray) -> tuple
def _se3(est: np.ndarray, gt: np.ndarray) -> tuple
def _sim3(est: np.ndarray, gt: np.ndarray) -> tuple
```

#### trajectory.py
```python
def extract_positions(poses: np.ndarray) -> np.ndarray
def extract_rotations(poses: np.ndarray) -> np.ndarray
def interpolate_trajectory(times: np.ndarray, poses: np.ndarray, target_times: np.ndarray) -> np.ndarray
def compute_path_length(poses: np.ndarray) -> float
```

**29 total core modules providing utility functions and classes**

### 4. Frontend (frontend/src/App.js)

**Monolithic component with all logic embedded:**

```javascript
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API = 'http://localhost:8007';

function App() {
  // State management (all in one component)
  const [view, setView] = useState('datasets');
  const [datasets, setDatasets] = useState([]);
  const [algorithms, setAlgorithms] = useState([]);
  const [runs, setRuns] = useState([]);
  const [ws, setWs] = useState(null);
  const [connected, setConnected] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const clientId = useRef(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  // WebSocket connection (inline)
  useEffect(() => {
    loadData();
    connectWebSocket();
    const interval = setInterval(loadData, 10000);
    return () => {
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, []);

  const connectWebSocket = () => {
    const socket = new WebSocket(`ws://localhost:8007/ws/${clientId.current}`);
    socket.onopen = () => { setConnected(true); addNotification('connected', 'success'); };
    socket.onclose = () => { setConnected(false); setTimeout(connectWebSocket, 3000); };
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'created' || data.type === 'updated' || data.type === 'deleted') {
        loadData();
      }
    };
    setWs(socket);
  };

  // Data loading (inline)
  const loadData = async () => {
    const [ds, alg, rn] = await Promise.all([
      fetch(`${API}/api/datasets`).then(r => r.json()).catch(() => ({ datasets: [] })),
      fetch(`${API}/api/algorithms`).then(r => r.json()).catch(() => ({ algorithms: [] })),
      fetch(`${API}/api/runs`).then(r => r.json()).catch(() => ({ runs: [] }))
    ]);
    setDatasets(ds.datasets || []);
    setAlgorithms(alg.algorithms || []);
    setRuns(rn.runs || []);
  };

  const addNotification = (message, type = 'info') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), 4000);
  };

  // Render (all views inline)
  return (
    <div className="app">
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        {/* Sidebar navigation */}
      </aside>
      <main className={`main-content ${sidebarOpen ? '' : 'expanded'}`}>
        {view === 'datasets' && <Datasets datasets={datasets} onUpdate={loadData} ... />}
        {view === 'algorithms' && <Algorithms algorithms={algorithms} onUpdate={loadData} ... />}
        {view === 'runs' && <Runs runs={runs} datasets={datasets} algorithms={algorithms} ... />}
        {view === 'results' && <Results runs={runs} ... />}
      </main>
      <div className="notifications">
        {/* Toast notifications */}
      </div>
    </div>
  );
}

// Inline view components (not separate files)
function Datasets({ datasets, onUpdate, onSelect, selected, addNotification }) { /* ... */ }
function Algorithms({ algorithms, onUpdate, addNotification }) { /* ... */ }
function Runs({ runs, datasets, algorithms, onUpdate, addNotification }) { /* ... */ }
function Results({ runs, onSelect, selected }) { /* ... */ }

export default App;
```

**No separate component files - everything in one 500+ line file**

### 5. Startup Script (start_openslam.sh)

```bash
#!/bin/bash
set -e

echo "========================================="
echo "   OpenSLAM v2.0 - Starting System"
echo "========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check/create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "Installing Node.js dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    cd frontend && npm install --silent && cd ..
fi

# Create directories
mkdir -p data uploads results cache temp logs plugins connectors

# Kill existing processes
lsof -ti:8007 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true

# Start backend
python3 run_backend.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Start frontend
cd frontend
SKIP_PREFLIGHT_CHECK=true ESLINT_NO_DEV_ERRORS=true npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo ""
echo "✓ System started successfully"
echo ""
echo "Frontend:  http://localhost:3001"
echo "Backend:   http://localhost:8007"
echo "API Docs:  http://localhost:8007/docs"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
```

### 6. Backend Launcher (run_backend.py)

```python
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
```

## Key Implementation Details

### Zero-Copy Dataset Loading

**Implementation in backend/api/main.py:**

```python
@app.post('/api/dataset/load')
async def load_dataset(data: dict = Body(...)):
    path_str = data.get('path')
    name = data.get('name')

    dataset_path = Path(path_str)
    if not dataset_path.exists():
        raise HTTPException(404, 'path does not exist')

    # ZERO-COPY: Store path reference only
    dataset_id = str(uuid.uuid4())[:8]
    fmt = format_detector.detect_format(dataset_path)

    # Generate preview IMMEDIATELY (no processing)
    preview_frames = _get_dataset_frames(dataset_path, fmt, max_frames=5)
    preview_data = {
        'frames': preview_frames,  # List of absolute file paths
        'count': len(preview_frames),
        'urls': [f'/api/dataset/{dataset_id}/frame/{i}' for i in range(len(preview_frames))]
    } if preview_frames else None

    datasets[dataset_id] = {
        'id': dataset_id,
        'name': name,
        'path': str(dataset_path),  # REFERENCE, not copy
        'format': fmt,
        'preview': preview_data,
        # ... other metadata
    }

    return datasets[dataset_id]
```

**Preview generation function:**

```python
def _get_dataset_frames(dataset_path: Path, dataset_format: str, max_frames: int = 5):
    frames = []

    if dataset_format == 'kitti':
        sequences_dir = dataset_path / 'sequences'
        if sequences_dir.exists():
            for seq_dir in sorted(sequences_dir.iterdir()):
                if seq_dir.is_dir():
                    for img_dir_name in ['image_0', 'image_2', 'image_left']:
                        img_dir = seq_dir / img_dir_name
                        if img_dir.exists():
                            img_files = sorted(img_dir.glob('*.png'))[:max_frames]
                            frames.extend([str(f) for f in img_files])
                            if len(frames) >= max_frames:
                                return frames[:max_frames]

    elif dataset_format == 'tum':
        rgb_dir = dataset_path / 'rgb'
        if rgb_dir.exists():
            img_files = sorted(rgb_dir.glob('*.png'))[:max_frames]
            frames = [str(f) for f in img_files]

    elif dataset_format == 'euroc':
        cam_dirs = [dataset_path / 'mav0' / 'cam0' / 'data',
                    dataset_path / 'mav0' / 'cam1' / 'data']
        for cam_dir in cam_dirs:
            if cam_dir.exists():
                img_files = sorted(cam_dir.glob('*.png'))[:max_frames]
                frames = [str(f) for f in img_files]
                if frames:
                    break

    else:
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            img_files = list(dataset_path.rglob(ext))[:max_frames]
            if img_files:
                frames = [str(f) for f in img_files]
                break

    return frames[:max_frames]
```

**Frame serving endpoint:**

```python
@app.get('/api/dataset/{dataset_id}/frame/{frame_index}')
async def get_dataset_frame(dataset_id: str, frame_index: int):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')

    ds = datasets[dataset_id]
    preview_frames = ds.get('preview', {}).get('frames', [])

    if frame_index < 0 or frame_index >= len(preview_frames):
        raise HTTPException(404, 'frame index out of range')

    frame_path = Path(preview_frames[frame_index])

    if not frame_path.exists():
        raise HTTPException(404, 'frame file not found')

    # Serve directly from original path (ZERO-COPY)
    return FileResponse(str(frame_path), media_type='image/png')
```

### WebSocket Real-Time Updates

**Implementation in backend/api/main.py:**

```python
ws_connections = {}

async def _broadcast_update(event: dict):
    for client_id, conn in list(ws_connections.items()):
        try:
            await conn['socket'].send_json(event)
        except:
            del ws_connections[client_id]

@app.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    ws_connections[client_id] = {'socket': websocket, 'connected': datetime.now().isoformat()}

    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        del ws_connections[client_id]

# Broadcast on dataset creation
await _broadcast_update({'type': 'dataset_created', 'dataset': datasets[dataset_id]})

# Broadcast on run update
await _broadcast_update({'type': 'run_updated', 'run': runs[run_id]})
```

### Frontend WebSocket Client

**Implementation in frontend/src/App.js:**

```javascript
const connectWebSocket = () => {
  const socket = new WebSocket(`ws://localhost:8007/ws/${clientId.current}`);

  socket.onopen = () => {
    setConnected(true);
    addNotification('connected', 'success');
  };

  socket.onclose = () => {
    setConnected(false);
    setTimeout(connectWebSocket, 3000);  // Auto-reconnect
  };

  socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'created' || data.type === 'updated' || data.type === 'deleted') {
      loadData();  // Refresh data
    }
  };

  setWs(socket);
};
```

## API Endpoints (Complete List)

### Dataset Management
- `POST /api/dataset/load` - Load dataset by path (zero-copy)
- `POST /api/upload` - Upload dataset file
- `GET /api/datasets` - List all datasets (with filters, sorting, pagination)
- `GET /api/dataset/{id}` - Get single dataset
- `GET /api/dataset/{id}/preview` - Get preview metadata
- `GET /api/dataset/{id}/frame/{index}` - Serve frame image (zero-copy)
- `GET /api/dataset/{id}/statistics` - Get dataset statistics
- `POST /api/dataset/{id}/process` - Process dataset (background)
- `DELETE /api/dataset/{id}` - Remove from registry

### Algorithm Management
- `POST /api/algorithm` - Create custom algorithm
- `GET /api/algorithms` - List all algorithms (with filters, sorting)
- `GET /api/algorithm/{id}` - Get single algorithm
- `DELETE /api/algorithm/{id}` - Remove from registry

### Execution Management
- `POST /api/run` - Create and start execution
- `GET /api/runs` - List all runs (with filters, sorting, pagination)
- `GET /api/run/{id}` - Get run details with progress
- `DELETE /api/run/{id}` - Cancel or remove run

### System
- `GET /` - Root endpoint (system info)
- `GET /api/health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /openapi.json` - OpenAPI schema
- `WS /ws/{client_id}` - WebSocket connection

## Configuration Files

### Frontend (frontend/craco.config.js)

```javascript
module.exports = {
  devServer: {
    port: 3001,
    allowedHosts: 'all',
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
  },
  webpack: {
    configure: (webpackConfig) => {
      // Remove ESLint plugin to avoid errors during development
      webpackConfig.plugins = webpackConfig.plugins.filter(
        plugin => plugin && plugin.constructor && plugin.constructor.name !== 'ESLintWebpackPlugin'
      );
      return webpackConfig;
    }
  }
};
```

### Frontend (frontend/package.json)

```json
{
  "name": "openslam-frontend",
  "version": "0.1.0",
  "dependencies": {
    "@craco/craco": "^7.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "plotly.js": "^2.35.3",
    "react-plotly.js": "^2.6.0",
    "react-router-dom": "^6.0.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "SKIP_PREFLIGHT_CHECK=true ESLINT_NO_DEV_ERRORS=true craco start",
    "build": "SKIP_PREFLIGHT_CHECK=true ESLINT_NO_DEV_ERRORS=true craco build",
    "test": "craco test",
    "eject": "react-scripts eject"
  },
  "proxy": "http://localhost:8007"
}
```

### Backend (requirements.txt)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
numpy>=1.24.0
opencv-python>=4.8.0
pyyaml>=6.0
websockets>=11.0
scipy>=1.11.0
h5py>=3.9.0
docker>=6.1.0
```

## Error Handling

### HTTP Error Responses

```python
# 404 Not Found
raise HTTPException(404, 'dataset not found')
raise HTTPException(404, 'algorithm not found')
raise HTTPException(404, 'frame file not found')
raise HTTPException(404, 'path does not exist')

# 400 Bad Request
raise HTTPException(400, 'path and name required')
raise HTTPException(400, 'path must be a directory')
raise HTTPException(400, 'dataset not processed')

# 500 Internal Server Error (automatic on exceptions)
```

### Error Object Format

```python
error = {
    'code': str,      # Error type code
    'message': str,   # Human-readable message
    'stderr': str     # Process stderr output (if applicable)
}
```

## Performance Characteristics

### Zero-Copy Architecture
- Dataset paths stored as references, NOT copied
- Preview generation scans filesystem but doesn't copy images
- Frame serving uses FileResponse (streaming)
- Typical dataset load: < 1 second regardless of size

### Memory Usage
- In-memory registry: ~1KB per dataset/algorithm/run entry
- No trajectory storage until evaluation requested
- Temporary files cleaned after processing

### Concurrency
- Async FastAPI endpoints (non-blocking)
- Background execution threads for algorithm runs
- WebSocket broadcasts (async)
- Frontend auto-refresh every 10 seconds + real-time WebSocket updates

## Security Considerations

### Path Validation
- Dataset paths checked for existence before registration
- Frame serving validates paths are within dataset preview list
- No arbitrary file access allowed

### Process Isolation
- Docker containers for untrusted algorithms
- Subprocess execution with timeout
- Resource limits configurable

### API Security
- CORS enabled for all origins (development mode)
- No authentication (single-user deployment)
- Input validation on all endpoints

## Testing

### Manual Testing
```bash
# Start system
./start_openslam.sh

# Test dataset loading
curl -X POST http://localhost:8007/api/dataset/load \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/dataset", "name": "Test"}'

# Test frame serving
curl http://localhost:8007/api/dataset/{id}/frame/0 -o frame.png

# Test health
curl http://localhost:8007/api/health
```

### Frontend Testing
```bash
cd frontend
npm test
```

### Backend Testing
```bash
# No automated tests currently
# Manual testing via Swagger UI at http://localhost:8007/docs
```

## Deployment

### Development (Current)
```bash
./start_openslam.sh
```

### Production (Future)
- Use gunicorn/uvicorn workers for backend
- Build frontend: `cd frontend && npm run build`
- Serve frontend static files with nginx
- Configure environment variables
- Setup logging and monitoring

## Recent Changes (Session History)

1. **Directory Organization** - Moved docs, examples, scripts, tests to subdirectories
2. **Config Import Fixes** - Fixed all core modules to import from `config` package
3. **Frontend Fixes** - Fixed craco.config.js for webpack-dev-server compatibility
4. **Backend Fixes** - Fixed run_backend.py to use environment variables
5. **Zero-Copy Preview** - Implemented immediate preview generation without file copying
6. **Frame Serving** - Added endpoint to serve frames directly from dataset path
7. **All Changes Committed** - 7 commits pushed to `claude/slam-research-analysis-011CV5NUzPChWgXnr6fazoij`

## Known Limitations

1. **No persistence** - All data in memory, lost on restart
2. **No authentication** - Single-user deployment only
3. **No database** - No permanent storage
4. **Monolithic frontend** - All logic in one component
5. **Monolithic backend** - All routes in one file
6. **No automated tests** - Manual testing only
7. **No production deployment** - Development mode only

## Future Improvements

1. Add database persistence (PostgreSQL/SQLite)
2. Split frontend into separate components
3. Split backend routes into separate modules
4. Add authentication and multi-user support
5. Add automated tests (unit, integration, E2E)
6. Add production deployment configuration
7. Add CI/CD pipeline
8. Add monitoring and logging
9. Add rate limiting
10. Add API versioning
