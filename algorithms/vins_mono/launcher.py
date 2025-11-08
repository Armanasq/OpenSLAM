#!/usr/bin/env python3

import json
import numpy as np
from typing import Dict, Any, Optional
from vins_mono_algorithm import VINSMono

def create_algorithm(config_path: str) -> VINSMono:
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    params = config.get('parameters', {})
    
    algorithm = VINSMono(
        max_features=params.get('max_features', {}).get('default', 150),
        min_distance=params.get('min_distance', {}).get('default', 30),
        focal_length=params.get('focal_length', {}).get('default', 460),
        loop_closure_threshold=params.get('loop_closure_threshold', {}).get('default', 0.3)
    )
    
    return algorithm

def get_algorithm_info() -> Dict[str, Any]:
    return {
        "name": "VINS-Mono",
        "type": "visual_inertial_slam",
        "input_types": ["monocular_image", "imu"],
        "output_types": ["pose", "trajectory", "sparse_map"],
        "real_time": True,
        "supports_loop_closure": True
    }

def validate_input(data: Dict[str, Any]) -> bool:
    required_keys = ['image', 'imu', 'timestamp']
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