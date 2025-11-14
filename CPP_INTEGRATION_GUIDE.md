# C++ SLAM Integration Guide

## Overview

OpenSLAM supports integrating C++ SLAM algorithms through multiple wrapper approaches. This guide explains how to integrate real C++ SLAM implementations like ORB-SLAM3, VINS-Mono, DSO, etc.

## Architecture

### Plugin Types

1. **Python Plugins**: Pure Python implementations, frame-by-frame processing
2. **C++ Plugins**: Compiled C++ SLAM systems, integrated via wrappers

### C++ Integration Methods

OpenSLAM supports three C++ integration methods:

#### 1. PyBind11 (Recommended for Frame-by-Frame)

**Pros**:
- Direct Python bindings to C++ code
- Frame-by-frame processing
- Low overhead
- Full control over SLAM state

**Cons**:
- Requires creating PyBind11 bindings
- Need to modify C++ code or create wrapper layer

**Use Case**: When you have C++ SLAM code that processes frames sequentially and you can create Python bindings.

#### 2. Subprocess (Batch Processing)

**Pros**:
- No code modification needed
- Works with pre-compiled binaries
- Easy to integrate existing SLAM systems

**Cons**:
- Batch processing only (all frames at once)
- Higher overhead
- Requires trajectory file output

**Use Case**: When you have a compiled SLAM executable that expects to run on all images at once.

#### 3. CTypes (Planned)

**Status**: Not yet implemented

**Use Case**: When you have a shared library (.so) with C-compatible API.

## Configuration

### Python Plugin Configuration

```yaml
name: "MySLAM"
version: "1.0.0"
language: python  # or omit for default
entry_point: "my_slam_wrapper.py"

functions:
  initialize: "slam_init"
  process_frame: "slam_track"
  get_current_pose: "slam_get_pose"
  shutdown: "slam_shutdown"

input_types: [image]
output_format: trajectory
```

### C++ Plugin Configuration

```yaml
name: "ORB-SLAM3"
version: "0.3.0"
language: cpp

input_types: [image, stereo, rgbd]
output_format: trajectory

cpp_wrapper:
  type: subprocess  # or pybind11, ctypes

  # Subprocess specific
  executable: "/path/to/orbslam3_mono"
  args:
    - "${vocab_path}"
    - "${settings_path}"
    - "${IMAGE_DIR}"
    - "${TRAJECTORY_FILE}"

  trajectory_extraction: file_based
  trajectory_format: tum  # or kitti

  # PyBind11 specific
  # module_path: "/path/to/orbslam3.so"
  # class_name: "System"
  # init_args: ["vocab_path", "settings_path"]

execution:
  timeout: 300
  max_memory_mb: 4096

default_params:
  vocab_path: "/path/to/ORBvoc.txt"
  settings_path: "/path/to/KITTI.yaml"
```

## Implementation Status

### Completed

1. **Core Infrastructure**
   - CPPSLAMWrapper class in `core/cpp_slam_wrapper.py`
   - Plugin manager C++ plugin detection
   - Plugin executor C++ plugin support
   - Configuration validation for C++ plugins

2. **Subprocess Wrapper**
   - Executable path resolution
   - Command line argument substitution
   - Environment variable support
   - Timeout management
   - Trajectory file parsing (TUM and KITTI formats)

3. **PyBind11 Wrapper**
   - Dynamic module loading
   - Class instantiation
   - Frame-by-frame processing support
   - Pose and trajectory extraction

4. **Example Plugin**
   - Mock ORB-SLAM3 plugin (`plugins/orbslam3_cpp/`)
   - Demonstrates subprocess approach
   - Mock executable for testing

### Current Limitations

1. **Subprocess Mode Architecture**
   - Current plugin_executor expects frame-by-frame processing
   - Subprocess C++ SLAM systems typically run in batch mode
   - **Architectural mismatch**: Need to reconcile these two models

2. **Solutions Needed**
   - Option A: Add batch processing mode to plugin_executor
   - Option B: Precompute trajectory during initialization (requires dataset upfront)
   - Option C: Focus on PyBind11 for frame-by-frame C++ integration

3. **Real SLAM Integration**
   - ORB-SLAM3 and VINS-Mono cloned from GitHub
   - Not yet compiled (requires extensive dependencies)
   - Need PyBind11 bindings for frame-by-frame integration

## Integration Examples

### Example 1: ORB-SLAM3 with PyBind11 (Recommended)

**Step 1**: Build ORB-SLAM3 with PyBind11 bindings

```cpp
// orbslam3_bindings.cpp
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "System.h"

namespace py = pybind11;

PYBIND11_MODULE(orbslam3, m) {
    py::class_<ORB_SLAM3::System>(m, "System")
        .def(py::init<const string &, const string &,
             ORB_SLAM3::System::eSensor>())
        .def("TrackMonocular", &ORB_SLAM3::System::TrackMonocular)
        .def("Shutdown", &ORB_SLAM3::System::Shutdown)
        .def("SaveTrajectoryTUM", &ORB_SLAM3::System::SaveTrajectoryTUM);
}
```

**Step 2**: Create Python wrapper

```python
# orbslam3_wrapper.py
import numpy as np
import orbslam3

def orbslam3_init(config):
    vocab_path = config['vocab_path']
    settings_path = config['settings_path']
    system = orbslam3.System(vocab_path, settings_path,
                              orbslam3.System.MONOCULAR)
    state = {'system': system, 'poses': []}
    return state, None

def orbslam3_track(state, frame_data):
    image = frame_data['image']
    timestamp = frame_data['timestamp']
    pose = state['system'].TrackMonocular(image, timestamp)
    state['poses'].append(pose)
    return {'success': True, 'pose': pose}, None
```

**Step 3**: Configure plugin

```yaml
name: "ORB-SLAM3-PyBind11"
language: cpp
cpp_wrapper:
  type: pybind11
  module_path: "/path/to/orbslam3.so"
  class_name: "System"
```

### Example 2: Subprocess Integration (Current Implementation)

**Current Challenge**: The subprocess approach requires all images upfront, but the plugin_executor provides images frame-by-frame.

**Workaround Options**:

1. **Batch Mode Plugin Executor** (Future Enhancement)
   ```python
   # New method in PluginExecutor
   def run_on_dataset_batch(self, dataset_path):
       # Load all images
       # Run C++ SLAM on all images
       # Parse trajectory
       # Return results
   ```

2. **Pre-Run Strategy**
   - Detect subprocess C++ plugins
   - Run SLAM once before frame processing
   - Cache trajectory
   - Serve cached poses during process_frame calls

### Example 3: Real ORB-SLAM3 Binary

**After Building ORB-SLAM3**:

```yaml
# plugins/orbslam3_real/slam_config.yaml
name: "ORB-SLAM3-Real"
language: cpp

cpp_wrapper:
  type: subprocess
  executable: "/home/user/ORB_SLAM3/Examples/Monocular/mono_kitti"
  args:
    - "/home/user/ORB_SLAM3/Vocabulary/ORBvoc.txt"
    - "${settings_path}"
    - "${IMAGE_DIR}"

  trajectory_extraction: file_based
  trajectory_format: tum
  output_file: "KeyFrameTrajectory.txt"
```

## Next Steps for Real Integration

### Short Term

1. **Build ORB-SLAM3** (Complex, many dependencies)
   ```bash
   cd /tmp/ORB_SLAM3
   # Install dependencies: OpenCV, Eigen, Pangolin, DBoW2, g2o
   ./build.sh
   ```

2. **Test with Compiled Binary**
   - Run mono_kitti on test dataset
   - Verify trajectory output format
   - Integrate with OpenSLAM

3. **Document Real Integration**
   - Add working example with real ORB-SLAM3
   - Provide compilation instructions
   - Create troubleshooting guide

### Medium Term

1. **Implement Batch Processing Mode**
   - Add `run_batch()` method to PluginExecutor
   - Support subprocess plugins properly
   - Maintain compatibility with frame-by-frame plugins

2. **Create PyBind11 Templates**
   - Provide binding examples for common SLAM APIs
   - Simplify integration process

3. **Add More C++ SLAM Systems**
   - VINS-Mono (visual-inertial)
   - DSO (direct method)
   - RTAB-Map (appearance-based)
   - LIO-SAM (LiDAR-inertial)

### Long Term

1. **ROS Integration**
   - Support ROS2 launch files
   - Direct topic subscription
   - Live SLAM evaluation

2. **Docker Containers**
   - Pre-built SLAM systems in containers
   - Easy deployment
   - Dependency isolation

3. **GPU Support**
   - CUDA-based SLAM systems
   - Accelerated feature extraction
   - Real-time performance

## Testing

### Mock Testing (Current)

```bash
cd /home/user/OpenSLAM

# List C++ plugins
python3 openslam.py list-plugins

# Test mock ORB-SLAM3 (once architecture fixed)
python3 openslam.py run-plugin orbslam3_cpp \
    --dataset data/kitti_00_100.txt \
    --format kitti \
    --output results/orbslam3_cpp/
```

### Real Testing (After Compilation)

```bash
# Build ORB-SLAM3
cd /tmp && git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git
cd ORB_SLAM3
# ... install dependencies ...
./build.sh

# Update plugin config with real paths
# Run evaluation
python3 openslam.py evaluate-plugin orbslam3_real \
    --dataset data/KITTI/00/ \
    --ground-truth data/KITTI/00_gt.txt \
    --format kitti
```

## Troubleshooting

### Common Issues

1. **Executable Not Found**
   - Check executable path in slam_config.yaml
   - Verify file has execute permissions
   - Ensure all dependencies are installed

2. **Trajectory File Not Generated**
   - Check SLAM output directory
   - Verify trajectory_file path in config
   - Check for SLAM errors in stderr

3. **Import Error for PyBind11 Module**
   - Verify .so file path
   - Check Python version compatibility
   - Ensure all C++ dependencies are linked

4. **Frame-by-Frame vs Batch**
   - Subprocess plugins: Use batch mode (when implemented)
   - PyBind11 plugins: Use standard frame-by-frame mode

## Architecture Decision

**Recommendation**: For production C++ SLAM integration, prioritize **PyBind11** approach:

1. Provides frame-by-frame control
2. Better integration with evaluation pipeline
3. Lower overhead than subprocess
4. Matches OpenSLAM architecture

**Subprocess approach**: Best for:
- Quick testing with pre-built binaries
- SLAM systems you don't control
- Batch processing workflows

## Files

- `core/cpp_slam_wrapper.py` - C++ wrapper implementation
- `core/plugin_executor.py` - Plugin execution with C++ support
- `core/plugin_manager.py` - C++ plugin loading
- `cpp_plugin_config.py` - C++ plugin configuration constants
- `plugins/orbslam3_cpp/` - Example C++ plugin
- `plugins/orbslam3_cpp/mock_orbslam3` - Mock executable for testing

## References

- ORB-SLAM3: https://github.com/UZ-SLAMLab/ORB_SLAM3
- VINS-Mono: https://github.com/HKUST-Aerial-Robotics/VINS-Mono
- PyBind11: https://pybind11.readthedocs.io/
