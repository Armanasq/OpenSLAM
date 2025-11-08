#!/usr/bin/env python3
"""
DSO Algorithm Launcher
Direct Sparse Odometry implementation
"""

import json
import numpy as np
from typing import Dict, Any, Optional
from dso_algorithm import DSO

def create_algorithm(config_path: str) -> DSO:
    """
    Create and configure DSO algorithm instance
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured DSO algorithm instance
    """
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Extract parameters
    params = config.get('parameters', {})
    
    # Create algorithm instance with parameters
    algorithm = DSO(
        photometric_threshold=params.get('photometric_threshold', {}).get('default', 7.0),
        gradient_threshold=params.get('gradient_threshold', {}).get('default', 8.0),
        max_points=params.get('max_points', {}).get('default', 2000),
        min_points=params.get('min_points', {}).get('default', 500)
    )
    
    return algorithm

def get_algorithm_info() -> Dict[str, Any]:
    """
    Get algorithm information
    
    Returns:
        Algorithm metadata
    """
    return {
        "name": "DSO",
        "type": "visual_odometry",
        "input_types": ["monocular_image"],
        "output_types": ["pose", "trajectory", "sparse_map"],
        "real_time": True,
        "supports_loop_closure": False
    }

def validate_input(data: Dict[str, Any]) -> bool:
    """
    Validate input data format
    
    Args:
        data: Input data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = ['image', 'timestamp']
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
    except Exception as e:
        print(f"Error creating algorithm: {e}")