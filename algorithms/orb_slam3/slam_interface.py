#!/usr/bin/env python3
"""
Standard SLAM Algorithm Interface
Base class that all SLAM algorithms must implement for OpenSLAM platform compatibility
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

class SLAMAlgorithmInterface(ABC):
    """
    Abstract base class for all SLAM algorithms in the OpenSLAM platform.
    
    This interface ensures consistent behavior across different SLAM implementations
    and enables plug-and-play algorithm swapping.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SLAM algorithm with configuration
        
        Args:
            config: Algorithm configuration dictionary loaded from config.json
        """
        self.config = config
        self.parameters = config.get('parameters', {})
        self.name = config.get('name', 'Unknown Algorithm')
        self.version = config.get('version', '1.0.0')
        
    @abstractmethod
    def initialize(self, **kwargs) -> bool:
        """
        Initialize the algorithm with given parameters
        
        Args:
            **kwargs: Initialization parameters (camera info, settings, etc.)
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
        
    @abstractmethod
    def process_frame(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single frame of sensor data
        
        Args:
            data: Dictionary containing sensor data with keys:
                - 'image': numpy array of image data
                - 'timestamp': float timestamp in seconds
                - 'imu': optional numpy array of IMU data [ax, ay, az, gx, gy, gz]
                - Additional sensor data as needed
                
        Returns:
            Dict containing:
                - 'success': bool indicating if processing succeeded
                - 'pose': numpy array (4,4) transformation matrix (if successful)
                - 'tracking_state': string describing current tracking state
                - 'error': string error message (if failed)
                - Additional algorithm-specific outputs
        """
        pass
        
    @abstractmethod
    def get_trajectory(self) -> List[np.ndarray]:
        """
        Get the complete estimated trajectory
        
        Returns:
            List of 4x4 transformation matrices representing the trajectory
        """
        pass
        
    @abstractmethod
    def reset(self) -> None:
        """
        Reset the algorithm state to initial conditions
        """
        pass
        
    def get_info(self) -> Dict[str, Any]:
        """
        Get algorithm information and current state
        
        Returns:
            Dictionary with algorithm metadata and current status
        """
        return {
            'name': self.name,
            'version': self.version,
            'category': self.config.get('category', 'Unknown'),
            'author': self.config.get('author', 'Unknown'),
            'description': self.config.get('description', ''),
            'supported_sensors': self.config.get('supported_sensors', []),
            'real_time_capable': self.config.get('real_time_capable', False)
        }
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current algorithm parameters
        
        Returns:
            Dictionary of current parameter values
        """
        return self.parameters.copy()
    
    def set_parameter(self, name: str, value: Any) -> bool:
        """
        Set a runtime parameter
        
        Args:
            name: Parameter name
            value: Parameter value
            
        Returns:
            bool: True if parameter was set successfully
        """
        if name in self.parameters:
            # Validate parameter type and range if specified in config
            param_config = self.config.get('parameters', {}).get(name, {})
            
            # Type validation
            expected_type = param_config.get('type')
            if expected_type:
                if expected_type == 'int' and not isinstance(value, int):
                    return False
                elif expected_type == 'float' and not isinstance(value, (int, float)):
                    return False
                elif expected_type == 'bool' and not isinstance(value, bool):
                    return False
                elif expected_type == 'string' and not isinstance(value, str):
                    return False
            
            # Range validation
            if 'min' in param_config and value < param_config['min']:
                return False
            if 'max' in param_config and value > param_config['max']:
                return False
            
            self.parameters[name] = value
            return True
        
        return False
    
    def validate_input(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate input data format
        
        Args:
            data: Input data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        input_format = self.config.get('input_format', {})
        
        # Check required fields
        if 'image' in input_format and 'image' not in data:
            return False, "Missing required 'image' field"
        
        if 'timestamp' in input_format and 'timestamp' not in data:
            return False, "Missing required 'timestamp' field"
        
        # Validate image format
        if 'image' in data:
            image = data['image']
            if not isinstance(image, np.ndarray):
                return False, "Image must be numpy array"
            
            if len(image.shape) not in [2, 3]:
                return False, "Image must be 2D (grayscale) or 3D (color)"
        
        # Validate IMU format if present
        if 'imu' in data:
            imu = data['imu']
            if not isinstance(imu, np.ndarray):
                return False, "IMU data must be numpy array"
            
            if imu.shape != (6,):
                return False, "IMU data must be 6-element array [ax, ay, az, gx, gy, gz]"
        
        return True, ""
    
    def get_output_format(self) -> Dict[str, str]:
        """
        Get the expected output format description
        
        Returns:
            Dictionary describing output format
        """
        return self.config.get('output_format', {})
    
    def get_computational_requirements(self) -> Dict[str, Any]:
        """
        Get computational requirements for this algorithm
        
        Returns:
            Dictionary with CPU, memory, and GPU requirements
        """
        return self.config.get('computational_requirements', {})
    
    def is_real_time_capable(self) -> bool:
        """
        Check if algorithm can run in real-time
        
        Returns:
            bool: True if real-time capable
        """
        return self.config.get('real_time_capable', False)
    
    def get_supported_sensors(self) -> List[str]:
        """
        Get list of supported sensor types
        
        Returns:
            List of supported sensor type strings
        """
        return self.config.get('supported_sensors', [])
    
    def shutdown(self) -> None:
        """
        Shutdown the algorithm and clean up resources
        
        Default implementation calls reset(). Override for custom cleanup.
        """
        self.reset()