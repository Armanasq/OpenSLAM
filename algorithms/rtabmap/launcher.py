#!/usr/bin/env python3
"""
RTAB-Map Algorithm Launcher
Real-Time Appearance-Based Mapping
"""

import json
import numpy as np
from typing import Dict, Any, Optional
from rtabmap_algorithm import RTABMap

def create_algorithm(config_path: str) -> RTABMap:
    """
    Create and configure RTAB-Map algorithm instance
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured RTAB-Map algorithm instance
    """
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Extract parameters
    params = config.get('parameters', {})
    
    # Create algorithm instance with parameters
    algorithm = RTABMap(
        memory_threshold=params.get('memory_threshold', {}).get('default', 100),
        similarity_threshold=params.get('similarity_threshold', {}).get('default', 0.2),
        max_features=params.get('max_features', {}).get('default', 400),
        depth_max=params.get('depth_max', {}).get('default', 4.0),
        voxel_size=params.get('voxel_size', {}).get('default', 0.01)
    )
    
    return algorithm

def get_algorithm_info() -> Dict[str, Any]:
    """
    Get algorithm information
    
    Returns:
        Algorithm metadata
    """
    return {
        "name": "RTAB-Map",
        "type": "rgbd_slam",
        "input_types": ["rgb_image", "depth_image", "camera_info"],
        "output_types": ["pose", "trajectory", "point_cloud", "occupancy_grid"],
        "real_time": True,
        "supports_loop_closure": True,
        "supports_relocalization": True,
        "multi_session": True
    }

def validate_input(data: Dict[str, Any]) -> bool:
    """
    Validate input data format
    
    Args:
        data: Input data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = ['rgb_image', 'depth_image', 'timestamp']
    return all(key in data for key in required_keys)

if __name__ == "__main__":
    # Test the launcher
    import os
    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    
    try:
        algorithm = create_algorithm(config_file)
        info = get_algorithm_info()
        print(f"Successfully created {info['name']} algorithm")
        print(f"Algorithm type: {info['type']}")
        print(f"Real-time capable: {info['real_time']}")
        print(f"Loop closure support: {info['supports_loop_closure']}")
        print(f"Multi-session support: {info['multi_session']}")
    except Exception as e:
        print(f"Error creating algorithm: {e}")