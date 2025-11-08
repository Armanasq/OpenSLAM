# OpenSLAM Algorithm Plugin System

This directory contains algorithm plugins for the OpenSLAM platform. Each algorithm is packaged as a self-contained plugin with standardized configuration and launcher files.

## Plugin Structure

Each algorithm plugin must follow this directory structure:

```
algorithms/
├── algorithm_name/
│   ├── config.json          # Algorithm metadata and configuration
│   ├── launcher.py          # Standardized execution interface
│   ├── algorithm.py         # Main algorithm implementation
│   ├── requirements.txt     # Python dependencies (optional)
│   ├── README.md           # Algorithm documentation (optional)
│   └── examples/           # Usage examples (optional)
```

## Configuration File (config.json)

The `config.json` file contains all metadata and configuration for the algorithm:

```json
{
  "name": "Algorithm Name",
  "version": "1.0.0",
  "category": "Visual SLAM",
  "description": "Brief description of the algorithm",
  "author": "Author Name",
  "email": "author@example.com",
  "license": "MIT",
  "paper_url": "https://arxiv.org/abs/...",
  "repository": "https://github.com/...",
  "tags": ["visual", "slam", "real-time"],
  "supported_sensors": ["camera", "imu"],
  "datasets_tested": ["KITTI", "EuRoC"],
  "performance": {
    "accuracy": 95,
    "speed": 88,
    "robustness": 92
  },
  "parameters": {
    "max_features": {
      "type": "int",
      "default": 1000,
      "min": 100,
      "max": 5000,
      "description": "Maximum number of features to extract"
    },
    "threshold": {
      "type": "float",
      "default": 0.01,
      "min": 0.001,
      "max": 0.1,
      "description": "Feature detection threshold"
    }
  },
  "input_format": {
    "images": "numpy array (H, W, 3) or (H, W)",
    "imu": "numpy array (6,) [ax, ay, az, gx, gy, gz]",
    "timestamps": "float (seconds)"
  },
  "output_format": {
    "pose": "numpy array (4, 4) transformation matrix",
    "trajectory": "list of (4, 4) transformation matrices",
    "landmarks": "numpy array (N, 3) 3D points"
  }
}
```

## Launcher Interface (launcher.py)

The `launcher.py` file provides a standardized interface for algorithm execution:

```python
from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

class SLAMAlgorithmInterface(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.parameters = config.get('parameters', {})

    @abstractmethod
    def initialize(self, **kwargs) -> bool:
        """Initialize the algorithm with given parameters"""
        pass

    @abstractmethod
    def process_frame(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single frame of sensor data"""
        pass

    @abstractmethod
    def get_trajectory(self) -> List[np.ndarray]:
        """Get the estimated trajectory"""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the algorithm state"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get algorithm information and current state"""
        return {
            'name': self.config.get('name', 'Unknown'),
            'version': self.config.get('version', '1.0.0'),
            'status': 'initialized'
        }
```

## Plugin Discovery

The system automatically discovers plugins by:

1. Scanning the `algorithms/` directory
2. Looking for valid `config.json` files
3. Validating the plugin structure
4. Loading algorithm metadata into the library

## Creating a New Plugin

1. Create a new directory under `algorithms/`
2. Add a valid `config.json` file
3. Implement the `launcher.py` with the standard interface
4. Add your algorithm implementation
5. The plugin will automatically appear in the Algorithm Library

## Example Plugin

See the `orb_slam3/` directory for a complete example implementation.
