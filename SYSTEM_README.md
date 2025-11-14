# OpenSLAM v2.0 - System Architecture & Integration Guide

Complete research-grade SLAM evaluation platform with zero-code integration, modern web interface, and comprehensive core functionality.

## 🚀 Quick Start

### Start the Complete System

```bash
./start_openslam.sh
```

This will:
1. Set up Python virtual environment
2. Install all dependencies (Python + Node.js)
3. Create required directories
4. Start FastAPI backend (port 8007)
5. Start React frontend (port 3001)

### Access the Application

- **Frontend UI**: http://localhost:3001
- **Backend API**: http://localhost:8007
- **API Documentation**: http://localhost:8007/docs

## 📁 System Architecture

```
OpenSLAM/
├── core/                          # Core Modules (All Integrated)
│   ├── plugin_manager.py         # Plugin discovery & validation
│   ├── plugin_executor.py        # SLAM algorithm execution
│   ├── connector_engine.py       # Zero-code data transformation
│   ├── workflow_executor.py      # Multi-stage workflow orchestration
│   ├── docker_orchestrator.py    # Container-based execution
│   ├── evaluation_metrics.py     # ATE/RPE calculation (ADDED)
│   ├── dataset_loader.py         # Dataset loading & format detection
│   ├── trajectory.py             # Trajectory processing
│   ├── metrics.py                # Metrics calculation
│   ├── visualization.py          # Plotting & visualization
│   ├── alignment.py              # Trajectory alignment
│   ├── export.py                 # Result export
│   ├── format_converter.py       # Format conversion
│   └── [... other core modules]
│
├── backend/                       # FastAPI Backend Server
│   ├── api/
│   │   └── main.py               # Main FastAPI application
│   ├── core/                     # Backend-specific utilities
│   │   ├── format_detector.py
│   │   ├── slam_interface.py
│   │   ├── metrics.py
│   │   └── visualizer.py
│   └── algorithms/               # Algorithm implementations
│
├── frontend/                      # React Web Application
│   ├── src/
│   │   ├── App.js                # Main React app
│   │   ├── components/           # React components
│   │   │   ├── DatasetManager.js
│   │   │   ├── AlgorithmDevelopment.js
│   │   │   ├── Visualization.js
│   │   │   ├── PerformanceAnalysis.js
│   │   │   └── [... other components]
│   │   └── config/
│   ├── public/
│   └── package.json
│
├── plugins/                       # SLAM Plugin Directory
│   ├── simple_workflow/          # Example zero-code plugin
│   └── [your plugins here]
│
├── connectors/                    # Data Transformation Connectors
│   ├── parsers/
│   │   └── tum_trajectory.yaml
│   ├── transforms/
│   │   └── identity.yaml
│   └── generators/
│
├── algorithms/                    # Pre-integrated SLAM Algorithms
│   ├── orb_slam3/
│   ├── vins_mono/
│   ├── dso/
│   ├── liosam/
│   └── rtabmap/
│
├── data/                          # Data Storage
├── results/                       # Evaluation Results
├── uploads/                       # File Uploads
├── logs/                          # System Logs
│
├── openslam.py                    # CLI Tool
├── run_backend.py                 # Backend starter
├── start_openslam.sh             # Complete system startup
├── config.py                      # System configuration
└── requirements.txt               # Python dependencies
```

## 🔧 Core Module Integration

### All Core Modules Fully Integrated

The system uses **ALL** core modules seamlessly:

####  1. **Plugin System**
- `core/plugin_manager.py` - Discovers and validates plugins
- `core/plugin_executor.py` - Executes SLAM algorithms
- Used by: Backend API, CLI tool

#### 2. **Zero-Code Workflow System**
- `core/connector_engine.py` - Data transformation engine
- `core/workflow_executor.py` - Multi-stage pipeline
- Supports: YAML-based configuration, no Python code needed

#### 3. **Evaluation & Metrics**
- `core/evaluation_metrics.py` - Calculate ATE, RPE
- `core/metrics.py` - Advanced metrics
- `core/trajectory.py` - Trajectory processing
- `core/alignment.py` - Trajectory alignment

#### 4. **Dataset Handling**
- `core/dataset_loader.py` - Load KITTI, EuRoC, TUM, ROS bags
- `core/format_converter.py` - Convert between formats
- `backend/core/format_detector.py` - Auto-detect formats

#### 5. **Visualization**
- `core/visualization.py` - 2D/3D trajectory plots
- `core/export.py` - Export to PNG, PDF, LaTeX
- `backend/core/visualizer.py` - Web-based visualization

#### 6. **Docker Integration**
- `core/docker_orchestrator.py` - Container execution
- Supports: Building Docker images, running containerized SLAM

#### 7. **Analysis Tools**
- `core/motion_analysis.py` - Motion pattern analysis
- `core/scene_analysis.py` - Scene complexity
- `core/statistical_analysis.py` - Statistical testing
- `core/task_metrics.py` - Task-specific metrics

## 🌐 Backend API (FastAPI)

### Complete REST API

**Base URL**: `http://localhost:8007`

#### Datasets
- `POST /api/dataset/load` - Load dataset from path
- `POST /api/upload` - Upload dataset file
- `GET /api/datasets` - List all datasets
- `GET /api/dataset/{id}` - Get dataset details
- `POST /api/dataset/{id}/process` - Process dataset
- `DELETE /api/dataset/{id}` - Delete dataset

#### Algorithms
- `POST /api/algorithm` - Create custom algorithm
- `GET /api/algorithms` - List algorithms
- `GET /api/algorithm/{id}` - Get algorithm details
- `DELETE /api/algorithm/{id}` - Delete algorithm

#### Evaluation Runs
- `POST /api/run` - Start evaluation
- `GET /api/runs` - List all runs
- `GET /api/run/{id}` - Get run details
- `DELETE /api/run/{id}` - Delete run

#### System
- `GET /` - System info
- `GET /api/health` - Health check
- `WebSocket /ws/{client_id}` - Real-time updates

### WebSocket Events

Real-time updates for:
- Dataset processing progress
- Evaluation progress
- Results completion
- System notifications

## 💻 Frontend (React)

### Features

1. **Dataset Manager**
   - Upload datasets (drag & drop)
   - Auto-format detection
   - Process datasets
   - Preview dataset structure

2. **Algorithm Development**
   - Create custom SLAM algorithms
   - Code editor with syntax highlighting
   - Test algorithms interactively

3. **Evaluation Runs**
   - Start evaluations
   - Monitor progress in real-time
   - View live metrics

4. **Results Visualization**
   - 3D trajectory plots
   - Metrics comparison
   - Error analysis
   - Export results

## 📊 Usage Examples

### CLI Tool

```bash
# Preview dataset
python openslam.py preview /path/to/dataset --detailed

# List plugins
python openslam.py list-plugins

# Run evaluation
python openslam.py evaluate my_plugin --dataset /path/to/data

# Compare multiple runs
python openslam.py compare run1.json run2.json run3.json

# Batch evaluation
python openslam.py batch batch_config.yaml
```

### Web Interface

1. **Add Dataset**
   - Click "add dataset"
   - Enter path or upload file
   - Auto-detected format

2. **Create Algorithm**
   - Click "create algorithm"
   - Write Python code (implements interface)
   - Save

3. **Run Evaluation**
   - Select dataset
   - Select algorithm
   - Click "start"
   - Monitor progress

4. **View Results**
   - Browse completed runs
   - View metrics
   - Compare trajectories
   - Export data

### Zero-Code Plugin

Create `plugins/my_plugin/slam_config.yaml`:

```yaml
name: "My SLAM Plugin"
version: "1.0.0"
input_types: [image]
output_format: trajectory

workflow:
  stages:
    - name: prepare
      type: prepare
      tasks:
        - name: load_trajectory
          connector: tum_trajectory
          config:
            input: "${DATASET_PATH}/groundtruth.txt"
          output: trajectory_data

    - name: extract
      type: extract
      tasks:
        - name: extract_poses
          connector: identity
          config:
            input: "${trajectory_data}"
          output: trajectory
```

No Python code needed!

## 🔌 Plugin Development

### Method 1: Python Plugin

```python
# plugins/my_slam/slam_interface.py
class SLAMInterface:
    def initialize(self, config):
        """Initialize SLAM system"""
        pass

    def process_frame(self, frame_data):
        """Process single frame"""
        return estimated_pose

    def finalize(self):
        """Get final trajectory"""
        return trajectory
```

### Method 2: Zero-Code Workflow

Just create YAML configuration - no coding required!

### Method 3: Docker Plugin

```yaml
# plugins/my_slam/slam_config.yaml
name: "Dockerized SLAM"
language: cpp

docker:
  image: "myslam:latest"
  build:
    context: "."
    dockerfile: "Dockerfile"
```

## 🗂️ File Organization

### Active Code (Production)
- `core/` - All core modules (fully integrated)
- `backend/` - FastAPI server
- `frontend/src/` - React application
- `plugins/` - SLAM plugins
- `connectors/` - Data connectors
- `algorithms/` - Pre-integrated algorithms

### Archived/Backup Code
- `others/flask_api_backup/` - Previous Flask API (replaced by FastAPI)
- `others/vanilla_js_scripts/` - Vanilla JS frontend (replaced by React)
- `others/vanilla_js_styles/` - Vanilla CSS (replaced by React)
- `others/vanilla_index.html` - Standalone HTML (replaced by React)

## 📦 Dependencies

### Python (requirements.txt)
- FastAPI - Web framework
- uvicorn - ASGI server
- numpy - Numerical computing
- scipy - Scientific computing
- matplotlib - Plotting
- opencv-python - Computer vision
- pyyaml - YAML parsing

### Node.js (frontend/package.json)
- React 18 - UI framework
- React Router - Navigation
- Plotly.js - Interactive charts
- Monaco Editor - Code editing
- xterm.js - Terminal emulation

## 🚦 System Status

### Check Backend
```bash
curl http://localhost:8007/api/health
```

### Check Logs
```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs
tail -f logs/frontend.log
```

### Stop System
```bash
# If started with start_openslam.sh
# Press Ctrl+C

# Or manually
kill $(cat .backend.pid)
kill $(cat .frontend.pid)
```

## 🔧 Configuration

Edit `config.py` to customize:
- Port numbers
- Directory paths
- Dataset formats
- Alignment methods
- Metrics configuration
- Visualization settings

## 📚 Documentation

- `README.md` - Project overview
- `API_README.md` - Backend API reference (archived)
- `PLUGIN_DEVELOPMENT_GUIDE.md` - Plugin development
- `ZERO_CODE_INTEGRATION.md` - Zero-code workflows
- `CPP_INTEGRATION_GUIDE.md` - C++ integration
- `SLAM_INTEGRATION_COOKBOOK.md` - Integration examples

## 🎯 Key Features

✅ **Zero-Code Integration** - Add SLAM algorithms without writing code
✅ **Modern Web Interface** - React-based UI with real-time updates
✅ **Comprehensive API** - FastAPI with WebSocket support
✅ **Multiple Formats** - KITTI, EuRoC, TUM, ROS bags
✅ **Docker Support** - Containerized SLAM execution
✅ **Advanced Metrics** - ATE, RPE, robustness, alignment
✅ **Visualization** - 2D/3D plots, error analysis
✅ **Batch Evaluation** - Run multiple configurations
✅ **CLI & Web** - Use via command line or browser

## 🤝 Contributing

All core modules are integrated and ready to use. To add new functionality:

1. Add core module in `core/`
2. Integrate with backend API in `backend/api/main.py`
3. Update frontend components in `frontend/src/components/`
4. Update this README

## 📄 License

MIT License - See LICENSE file for details

---

**OpenSLAM v2.0** - Research-Grade SLAM Evaluation Platform
