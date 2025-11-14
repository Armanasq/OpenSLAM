# OpenSLAM Plugin Development Guide

## Overview

The OpenSLAM plugin system allows you to integrate your SLAM algorithm into the evaluation framework through a configuration-based routing system. You define how your SLAM code connects to our evaluation pipeline using a YAML configuration file.

## Plugin Architecture

```
plugins/
  my_slam/
    slam_config.yaml       # Configuration and routing definitions
    slam_wrapper.py        # Python wrapper for your SLAM code
    lib/                   # Your SLAM libraries
    vocabulary/            # Algorithm-specific files
    config/                # Algorithm configurations
```

## Quick Start

### Step 1: Create Plugin Directory

```bash
mkdir -p plugins/my_slam
cd plugins/my_slam
```

### Step 2: Write Configuration File

Create `slam_config.yaml`:

```yaml
name: "MySLAM"
version: "1.0.0"
entry_point: "slam_wrapper.py"

functions:
  initialize: "slam_init"
  process_frame: "slam_track"
  get_current_pose: "get_camera_pose"
  get_full_trajectory: "get_trajectory"
  shutdown: "slam_shutdown"

input_types: ["image", "stereo"]
output_format: "trajectory"
```

### Step 3: Create Wrapper Code

Create `slam_wrapper.py` that implements the required functions:

```python
import numpy as np
# Import your SLAM library
# from my_slam_lib import SLAM

def slam_init(config):
    """Initialize SLAM system"""
    # Your initialization code
    state = {}  # Your SLAM state object
    return state, None  # Return (state, error)

def slam_track(state, frame_data):
    """Process single frame"""
    # frame_data contains: index, timestamp, image, pose (optional)
    # Your tracking code
    result = {'success': True}
    return result, None

def get_camera_pose(state):
    """Get current pose as 4x4 SE(3) matrix"""
    pose = np.eye(4)  # Your current pose
    return pose, None

def get_trajectory(state):
    """Get full trajectory as Nx4x4 array"""
    trajectory = np.array([])  # Your trajectory
    return trajectory, None

def slam_shutdown(state):
    """Cleanup resources"""
    # Your cleanup code
    return True, None
```

### Step 4: Test Your Plugin

```bash
# List available plugins
python openslam.py list-plugins

# Test your plugin on a dataset
python openslam.py run-plugin my_slam \
    --dataset data/test/ground_truth_kitti.txt \
    --format kitti \
    --output results/my_slam

# Evaluate against ground truth
python openslam.py eval-plugin my_slam \
    --dataset data/test/ground_truth_kitti.txt \
    --ground-truth data/test/ground_truth_kitti.txt \
    --format kitti \
    --output results/my_slam
```

## Function Routing

The plugin system provides a **routing mechanism** that maps your SLAM functions to the evaluation pipeline:

### Required Functions

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `initialize` | Setup SLAM system | config dict | state object |
| `process_frame` | Track single frame | state, frame_data | result dict |
| `get_current_pose` | Get current pose | state | 4x4 matrix |
| `shutdown` | Cleanup | state | success bool |

### Optional Functions

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `get_full_trajectory` | Get all poses | state | Nx4x4 array |
| `get_map` | Get map points | state | Nx3 array |
| `reset` | Reset SLAM | state | success bool |
| `get_tracking_status` | Get status | state | status string |

## Data Adapters

Data adapters transform dataset formats into your SLAM's expected input format.

### Creating Custom Adapters

```python
class MyDataAdapter:
    def __init__(self, dataset):
        self.dataset = dataset
        # Extract poses/timestamps from dataset

    def get_frame_data(self, index):
        """Return frame data in your SLAM's format"""
        frame_data = {
            'index': index,
            'timestamp': self.timestamps[index],
            'image': self.load_image(index),
            'depth': self.load_depth(index)  # if needed
        }
        return frame_data
```

Register in config:

```yaml
data_adapters:
  kitti: "MyKITTIAdapter"
  tum: "MyTUMAdapter"
  custom: "MyGenericAdapter"
```

## Data Routing Map

Define how data flows between components:

```yaml
data_routing:
  # Input routing (dataset → SLAM)
  image_path: "frame_data.image"
  depth_path: "frame_data.depth"
  timestamp: "frame_data.timestamp"

  # Output routing (SLAM → evaluation)
  pose_matrix: "state.current_pose"
  trajectory: "state.all_poses"
  map_points: "state.map.points"
  tracking_status: "state.tracker.status"
```

## Configuration Parameters

### Default Parameters

```yaml
default_params:
  # These are passed to your initialize() function
  vocab_path: "vocabulary/ORBvoc.txt"
  config_path: "config/kitti.yaml"
  num_features: 2000
  use_viewer: false
```

### Dependencies

```yaml
dependencies:
  python:
    - numpy>=1.21.0
    - opencv-python>=4.5.0
  system:
    - cmake>=3.10
    - gcc>=7.0
  files:
    - vocabulary/ORBvoc.txt
    - config/kitti.yaml
```

### Environment Variables

```yaml
environment:
  PYTHONPATH: "${PLUGIN_DIR}/python"
  LD_LIBRARY_PATH: "${PLUGIN_DIR}/lib"
  MY_SLAM_ROOT: "${PLUGIN_DIR}"
```

## Advanced Features

### Multi-Sensor Input

```yaml
input_types:
  - stereo
  - imu
  - lidar

functions:
  process_frame:
    name: "slam_track"
    inputs:
      - type: "stereo"
        left: "frame_data.image_left"
        right: "frame_data.image_right"
      - type: "imu"
        data: "frame_data.imu"
```

### Execution Control

```yaml
execution:
  timeout: 300              # seconds
  max_memory: "8GB"
  parallel: false           # process frames in parallel
  warmup_frames: 10         # frames to skip for initialization
  max_frame_time: 10.0      # max seconds per frame
```

### Output Formats

```yaml
output_format: "trajectory"  # or "pose", "map", "pointcloud"

output_options:
  save_trajectory: true
  save_map: true
  save_timing: true
  export_format: ["tum", "kitti"]
```

## Example: Integrating ORB-SLAM3

```yaml
name: "ORB-SLAM3"
version: "1.0"
entry_point: "orbslam3_wrapper.py"

functions:
  initialize: "orb_init"
  process_frame: "orb_track_mono"
  get_current_pose: "orb_get_pose"
  get_full_trajectory: "orb_get_trajectory"
  shutdown: "orb_shutdown"

input_types: ["image", "stereo", "rgbd"]
output_format: "trajectory"

data_adapters:
  kitti: "ORBKITTIAdapter"
  tum: "ORBTUMAdapter"
  euroc: "ORBEuRoCAdapter"

default_params:
  vocab_path: "vocabulary/ORBvoc.txt"
  settings_path: "config/KITTI00-02.yaml"
  sensor_type: "monocular"

dependencies:
  python:
    - numpy
    - opencv-python
  files:
    - vocabulary/ORBvoc.txt
    - config/KITTI00-02.yaml
```

## Example: Integrating LIO-SAM

```yaml
name: "LIO-SAM"
version: "1.0"
entry_point: "liosam_wrapper.py"

functions:
  initialize: "liosam_init"
  process_frame: "liosam_process"
  get_current_pose: "liosam_pose"
  get_full_trajectory: "liosam_trajectory"
  shutdown: "liosam_stop"

input_types: ["lidar", "imu"]
output_format: "trajectory"

data_routing:
  lidar_points: "frame_data.pointcloud"
  imu_data: "frame_data.imu"
  pose_matrix: "state.odometry.pose"

default_params:
  config_path: "config/params.yaml"
  map_resolution: 0.1
```

## Validation

The plugin system validates:

✅ All required functions are defined
✅ Input/output types are supported
✅ Entry point file exists
✅ Configuration syntax is correct
✅ Data adapters are implemented

## Best Practices

1. **Error Handling**: Return `(result, error)` tuples from all functions
2. **State Management**: Keep all SLAM state in the state object
3. **Memory**: Release resources in `shutdown()`
4. **Thread Safety**: Ensure functions are thread-safe if `parallel: true`
5. **Testing**: Test with small datasets first
6. **Documentation**: Document your function parameters and return values

## Debugging

Enable verbose output:

```bash
python openslam.py run-plugin my_slam --dataset data --verbose
```

Check plugin validation:

```bash
python openslam.py validate-plugin my_slam
```

## Support

See `example_plugin_wrapper.py` for a complete working example.
