# OpenSLAM v0.1

<div align="center">

![OpenSLAM Logo](logo.jpg)

**Interactive SLAM Development Platform**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.0+-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.100+-green.svg)](https://fastapi.tiangolo.com/)

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## 📖 Overview

OpenSLAM is a comprehensive web-based platform for learning, developing, and researching Simultaneous Localization and Mapping (SLAM) algorithms. It provides an integrated environment that combines dataset management, algorithm development, real-time visualization, and performance analysis in a single, user-friendly interface.

### 🎯 Key Highlights

- **🌐 Web-Based**: No installation required - access everything through your browser
- **🔌 Plugin Architecture**: Easy integration of custom SLAM algorithms
- **📊 Real-Time Visualization**: 3D trajectory and point cloud rendering
- **🎓 Interactive Tutorials**: Learn SLAM concepts hands-on
- **⚡ Live Development**: Integrated IDE with terminal and debugger
- **📈 Performance Analysis**: Comprehensive metrics (ATE, RPE) and comparison tools

---

## ✨ Features

### 🗂️ Dataset Management

- **KITTI Format Support**: Load and validate KITTI datasets
- **Multi-Sensor Data**: Handle camera images, LiDAR point clouds, IMU data
- **Ground Truth Integration**: Automatic trajectory comparison
- **Directory Browser**: Easy dataset selection with file system navigation
- **Frame Preview**: Visualize dataset frames before processing

### ⚡ Algorithm Development

- **Monaco Code Editor**: Professional IDE experience with syntax highlighting
- **File Explorer**: Navigate and edit algorithm files
- **Integrated Terminal**: Run commands directly in the browser
- **Code Execution**: Test algorithms with real-time feedback
- **Plugin System**: Standardized interface for algorithm integration

### 📊 Visualization

- **3D Trajectory Rendering**: Interactive camera path visualization
- **Point Cloud Display**: Real-time LiDAR data rendering
- **Ground Truth Overlay**: Compare estimated vs. actual trajectories
- **Multi-Camera View**: Simultaneous display of multiple camera feeds
- **Frame-by-Frame Playback**: Step through dataset sequences

### 🔬 Performance Analysis

- **Standard Metrics**: ATE (Absolute Trajectory Error), RPE (Relative Pose Error)
- **Algorithm Comparison**: Side-by-side performance evaluation
- **Statistical Analysis**: Detailed metric breakdowns
- **Export Capabilities**: Save results as CSV/JSON
- **Visual Reports**: Automatic plot generation

### 🎓 Tutorial System

- **Interactive Learning**: Step-by-step SLAM tutorials
- **Code Templates**: Pre-built examples for common tasks
- **Solution Validation**: Automatic feedback on implementations
- **Progress Tracking**: Monitor learning advancement

### 🔧 Supported Algorithms

- **ORB-SLAM3**: Feature-based visual SLAM
- **VINS-Mono**: Monocular visual-inertial SLAM
- **LIO-SAM**: LiDAR-inertial odometry
- **RTABMap**: RGB-D graph-based SLAM
- **DSO**: Direct sparse odometry

---

## 🚀 Installation

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 16.0 or higher
- **npm**: 8.0 or higher
- **Docker** (optional): For containerized deployment

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/OpenSLAM.git
cd OpenSLAM/OpenSLAM_v0.1
```

#### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export OPENSLAM_DATA_DIR=/path/to/your/datasets
export OPENSLAM_LOG_DIR=/path/to/logs
export OPENSLAM_TEMP_DIR=/path/to/temp

# Run the backend server
python run_backend.py
```

The backend will start on `http://localhost:8007`

#### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm start
```

The frontend will start on `http://localhost:3001`

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

Access the application at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 📚 Usage

### Loading a Dataset

1. Navigate to the **Datasets** page
2. Click **"📁 Browse Directories"**
3. Navigate to your KITTI dataset folder
4. Click **"Select This Directory"**
5. Click **"Load Dataset"**

The platform will automatically validate the dataset structure and load calibration data.

### Developing an Algorithm

1. Go to the **Algorithms** page
2. Select an algorithm template or create a new one
3. Write your algorithm code in the Monaco editor
4. Click **"Validate Code"** to check for syntax errors
5. Select a dataset for testing
6. Click **"Execute Algorithm"**
7. View results in the **Visualization** tab

### Comparing Algorithms

1. Execute multiple algorithms on the same dataset
2. Navigate to the **Analysis** page
3. Select algorithms to compare
4. View side-by-side metrics and plots
5. Export results for further analysis

### Following Tutorials

1. Click on **Tutorials** in the navigation
2. Select a tutorial from the list
3. Read the step description
4. Write code in the provided editor
5. Click **"Submit Solution"** for validation
6. Progress to the next step upon success

---

## 🏗️ Architecture

```
OpenSLAM_v0.1/
├── frontend/              # React frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.js         # Main application
│   │   └── index.js       # Entry point
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
│
├── backend/               # FastAPI backend server
│   ├── api/               # API endpoints
│   ├── core/              # Core modules
│   │   ├── dataset_manager.py
│   │   ├── algorithm_loader.py
│   │   ├── code_executor.py
│   │   └── ...
│   ├── algorithms/        # Built-in algorithms
│   └── requirements.txt   # Python dependencies
│
├── algorithms/            # Algorithm plugins
│   ├── orb_slam3/
│   ├── vins_mono/
│   ├── liosam/
│   ├── rtabmap/
│   └── dso/
│
├── shared/                # Shared models and interfaces
│   ├── models.py          # Pydantic models
│   └── interfaces.py      # Abstract base classes
│
├── config/                # Configuration files
│   └── settings.py        # Application settings
│
└── docker-compose.yml     # Docker configuration
```

### Technology Stack

**Frontend:**

- React 18
- React Router
- Monaco Editor
- Plotly.js
- Three.js
- WebSocket

**Backend:**

- FastAPI
- Pydantic
- NumPy
- OpenCV
- WebSocket
- PTY (Terminal)

---

## 🔌 API Documentation

Once the backend is running, visit `http://localhost:8007/docs` for interactive API documentation powered by Swagger UI.

### Key Endpoints

**Datasets:**

- `GET /api/datasets` - List all datasets
- `POST /api/datasets/load` - Load a new dataset
- `GET /api/datasets/{id}/details` - Get dataset details
- `POST /api/browse-directory` - Browse file system

**Algorithms:**

- `GET /api/algorithms/library` - List available algorithms
- `POST /api/algorithms/{id}/load` - Load algorithm plugin
- `POST /api/execute-algorithm` - Run algorithm

**Analysis:**

- `POST /api/analysis/compare` - Compare algorithms
- `GET /api/analysis/plots/{id}` - Get comparison plots

**WebSocket:**

- `WS /ws` - Main WebSocket connection
- `WS /ws/terminal` - Terminal I/O
- `WS /ws/execution` - Algorithm execution updates

---

## 🧩 Creating Custom Algorithms

### Plugin Structure

```
my_algorithm/
├── config.json           # Algorithm metadata
├── launcher.py           # Entry point
├── algorithm.py          # Implementation
├── README.md            # Documentation
└── requirements.txt     # Dependencies (optional)
```

### config.json Example

```json
{
  "name": "My SLAM Algorithm",
  "category": "Visual SLAM",
  "description": "Description of your algorithm",
  "author": "Your Name",
  "version": "1.0.0",
  "sensors": ["camera", "imu"],
  "parameters": {
    "feature_threshold": 0.01,
    "max_features": 1000
  }
}
```

### launcher.py Example

```python
from shared.interfaces import SLAMAlgorithm
import numpy as np

class MyAlgorithm(SLAMAlgorithm):
    def initialize(self, config):
        # Initialize your algorithm
        return True

    def process_frame(self, frame_data):
        # Process a single frame
        return {
            "pose": np.eye(4),
            "features": []
        }

    def get_trajectory(self):
        # Return full trajectory
        return np.array([])

    def get_map(self):
        # Return map points
        return None
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

---

## 📊 Performance

- **Dataset Loading**: < 2 seconds for KITTI sequences
- **Frame Processing**: 30-60 FPS depending on algorithm
- **Visualization**: 60 FPS for trajectories, 30 FPS for point clouds
- **WebSocket Latency**: < 50ms for real-time updates

---

## 🛠️ Configuration

### Environment Variables

```bash
# Data directory
export OPENSLAM_DATA_DIR=/path/to/datasets

# Log directory
export OPENSLAM_LOG_DIR=/path/to/logs

# Temporary files
export OPENSLAM_TEMP_DIR=/path/to/temp

# Backend port
export OPENSLAM_BACKEND_PORT=8007

# Frontend port
export OPENSLAM_FRONTEND_PORT=3001
```

### config/settings.py

Modify `config/settings.py` to customize:

- Directory paths
- Server ports
- Algorithm parameters
- Logging levels

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.10+

# Install dependencies
pip install -r requirements.txt

# Check port availability
lsof -i :8007
```

### Frontend won't start

```bash
# Check Node.js version
node --version  # Should be 16.0+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check port availability
lsof -i :3001
```

### Dataset loading fails

- Ensure dataset follows KITTI format
- Check file permissions
- Verify `calib.txt` and `times.txt` exist
- Check console for detailed error messages

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint for JavaScript code
- Write tests for new features
- Update documentation
- Add comments for complex logic

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **KITTI Dataset**: For providing benchmark datasets
- **ORB-SLAM3**: Carlos Campos et al.
- **VINS-Mono**: Tong Qin et al.
- **FastAPI**: Sebastián Ramírez
- **React**: Facebook Open Source

---

## 📧 Contact

- **Project Maintainer**: [Your Name]
- **Email**: your.email@example.com
- **GitHub**: [@yourusername](https://github.com/yourusername)
- **Issues**: [GitHub Issues](https://github.com/yourusername/OpenSLAM/issues)

---

## 🗺️ Roadmap

### v0.2 (Planned)

- [ ] Multi-dataset format support (EuRoC, TUM RGB-D)
- [ ] Enhanced 3D visualization with Three.js
- [ ] Real-time algorithm debugging
- [ ] Parameter tuning interface

### v0.3 (Planned)

- [ ] User authentication and authorization
- [ ] Multi-user collaboration
- [ ] Cloud dataset storage
- [ ] Automated benchmarking suite

### v1.0 (Future)

- [ ] Production-ready deployment
- [ ] Advanced machine learning integration
- [ ] Mobile app support
- [ ] Enterprise features

---

## 📈 Project Status

**Current Version**: 0.1.0  
**Status**: Active Development  
**Last Updated**: November 2025

---

<div align="center">

**Made with ❤️ for the SLAM community**

[⬆ Back to Top](#openslam-v01)

</div>
