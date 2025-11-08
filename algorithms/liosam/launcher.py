#!/usr/bin/env python3

import json
import numpy as np
from typing import Dict, Any, Optional
from liosam_algorithm import LIOSAM

def create_algorithm(config_path: str) -> LIOSAM:
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    params = config.get('parameters', {})
    
    algorithm = LIOSAM(
        voxel_size=params.get('voxel_size', {}).get('default', 0.1),
        icp_threshold=params.get('icp_threshold', {}).get('default', 0.3),
        loop_closure_radius=params.get('loop_closure_radius', {}).get('default', 15.0),
        keyframe_distance=params.get('keyframe_distance', {}).get('default', 1.0)
    )
    
    return algorithm

def get_algorithm_info() -> Dict[str, Any]:
    return {
        "name": "LIO-SAM",
        "type": "lidar_inertial_slam",
        "input_types": ["lidar_pointcloud", "imu", "gps"],
        "output_types": ["pose", "trajectory", "point_cloud_map"],
        "real_time": True,
        "supports_loop_closure": True
    }

def validate_input(data: Dict[str, Any]) -> bool:
    required_keys = ['pointcloud', 'imu', 'timestamp']
    return all(key in data for key in required_keys)

if __name__ == "__main__":
    import os
    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    
    try:
        algorithm = create_algorithm(config_file)
        info = get_algorithm_info()
        print(f"Successfully created {info['name']} algorithm")
        print(f"Algorithm type: {info['type']}")
        print(f"Real-time capable: {info['real_time']}")
    except Exception as e:
        print(f"Error creating algorithm: {e}")