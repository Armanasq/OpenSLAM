#!/usr/bin/env python3
"""
Algorithm Plugin Loader
Automatically discovers and loads algorithm plugins from the algorithms directory
"""

import os
import json
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AlgorithmLoader:
    """
    Loads and manages algorithm plugins from the algorithms directory
    """
    
    def __init__(self, algorithms_dir: str = "algorithms"):
        """
        Initialize the algorithm loader
        
        Args:
            algorithms_dir: Path to the algorithms directory
        """
        self.algorithms_dir = Path(algorithms_dir)
        self.loaded_algorithms = {}
        self.algorithm_configs = {}
        
    def discover_algorithms(self) -> List[Dict[str, Any]]:
        """
        Discover all valid algorithm plugins in the algorithms directory
        
        Returns:
            List of algorithm configuration dictionaries
        """
        algorithms = []
        
        if not self.algorithms_dir.exists():
            logger.warning(f"Algorithms directory {self.algorithms_dir} does not exist")
            return algorithms
        
        # Scan each subdirectory
        for algorithm_dir in self.algorithms_dir.iterdir():
            if not algorithm_dir.is_dir():
                continue
                
            config_file = algorithm_dir / "config.json"
            launcher_file = algorithm_dir / "launcher.py"
            
            # Check if required files exist
            if not config_file.exists():
                logger.warning(f"Algorithm {algorithm_dir.name}: missing config.json")
                continue
                
            if not launcher_file.exists():
                logger.warning(f"Algorithm {algorithm_dir.name}: missing launcher.py")
                continue
            
            try:
                # Load and validate configuration
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Validate required fields
                required_fields = ['name', 'category', 'description', 'author']
                missing_fields = [field for field in required_fields if field not in config]
                
                if missing_fields:
                    logger.error(f"Algorithm {algorithm_dir.name}: missing required fields: {missing_fields}")
                    continue
                
                # Add plugin metadata
                config['plugin_id'] = algorithm_dir.name
                config['plugin_path'] = str(algorithm_dir)
                config['config_file'] = str(config_file)
                config['launcher_file'] = str(launcher_file)
                
                # Check for optional files
                config['has_readme'] = (algorithm_dir / "README.md").exists()
                config['has_requirements'] = (algorithm_dir / "requirements.txt").exists()
                config['has_examples'] = (algorithm_dir / "examples").exists()
                
                # Validate launcher interface
                if self._validate_launcher(launcher_file):
                    algorithms.append(config)
                    self.algorithm_configs[algorithm_dir.name] = config
                    logger.info(f"Discovered algorithm: {config['name']} v{config.get('version', '1.0.0')}")
                else:
                    logger.error(f"Algorithm {algorithm_dir.name}: invalid launcher interface")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Algorithm {algorithm_dir.name}: invalid JSON in config.json: {e}")
            except Exception as e:
                logger.error(f"Algorithm {algorithm_dir.name}: error loading config: {e}")
        
        logger.info(f"Discovered {len(algorithms)} valid algorithm plugins")
        return algorithms
    
    def _validate_launcher(self, launcher_file: Path) -> bool:
        """
        Validate that the launcher file implements the required interface
        
        Args:
            launcher_file: Path to the launcher.py file
            
        Returns:
            bool: True if launcher is valid
        """
        try:
            # Add algorithm directory to Python path temporarily
            algorithm_dir = str(launcher_file.parent)
            if algorithm_dir not in sys.path:
                sys.path.insert(0, algorithm_dir)
            
            try:
                # Load the launcher module
                spec = importlib.util.spec_from_file_location("launcher", launcher_file)
                if spec is None or spec.loader is None:
                    return False
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            finally:
                # Remove from path
                if algorithm_dir in sys.path:
                    sys.path.remove(algorithm_dir)
            
            # Check for required factory function
            if not hasattr(module, 'create_algorithm'):
                logger.error(f"Launcher {launcher_file}: missing create_algorithm function")
                return False
            
            # Check if the factory function is callable
            if not callable(module.create_algorithm):
                logger.error(f"Launcher {launcher_file}: create_algorithm is not callable")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating launcher {launcher_file}: {e}")
            return False
    
    def load_algorithm(self, plugin_id: str, **kwargs) -> Optional[Any]:
        """
        Load and instantiate an algorithm plugin
        
        Args:
            plugin_id: The plugin identifier (directory name)
            **kwargs: Additional arguments to pass to the algorithm
            
        Returns:
            Algorithm instance or None if loading failed
        """
        if plugin_id not in self.algorithm_configs:
            logger.error(f"Algorithm plugin {plugin_id} not found")
            return None
        
        config = self.algorithm_configs[plugin_id]
        launcher_file = Path(config['launcher_file'])
        
        try:
            # Load the launcher module
            spec = importlib.util.spec_from_file_location(f"launcher_{plugin_id}", launcher_file)
            if spec is None or spec.loader is None:
                logger.error(f"Failed to load launcher spec for {plugin_id}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # Add algorithm directory to Python path temporarily
            algorithm_dir = str(Path(config['plugin_path']))
            if algorithm_dir not in sys.path:
                sys.path.insert(0, algorithm_dir)
            
            try:
                spec.loader.exec_module(module)
                
                # Create algorithm instance
                algorithm = module.create_algorithm(config['config_file'])
                
                # Store reference
                self.loaded_algorithms[plugin_id] = algorithm
                
                logger.info(f"Successfully loaded algorithm: {config['name']}")
                return algorithm
                
            finally:
                # Remove from path
                if algorithm_dir in sys.path:
                    sys.path.remove(algorithm_dir)
                
        except Exception as e:
            logger.error(f"Error loading algorithm {plugin_id}: {e}")
            return None
    
    def get_algorithm_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get algorithm configuration information
        
        Args:
            plugin_id: The plugin identifier
            
        Returns:
            Algorithm configuration dictionary or None
        """
        return self.algorithm_configs.get(plugin_id)
    
    def list_algorithms(self) -> List[str]:
        """
        Get list of available algorithm plugin IDs
        
        Returns:
            List of plugin identifiers
        """
        return list(self.algorithm_configs.keys())
    
    def validate_algorithm_directory(self, algorithm_dir: Path) -> tuple[bool, List[str]]:
        """
        Validate an algorithm directory structure
        
        Args:
            algorithm_dir: Path to algorithm directory
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not algorithm_dir.is_dir():
            errors.append("Path is not a directory")
            return False, errors
        
        # Check required files
        config_file = algorithm_dir / "config.json"
        launcher_file = algorithm_dir / "launcher.py"
        
        if not config_file.exists():
            errors.append("Missing config.json file")
        
        if not launcher_file.exists():
            errors.append("Missing launcher.py file")
        
        if errors:
            return False, errors
        
        # Validate config.json
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            required_fields = ['name', 'category', 'description', 'author']
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field in config.json: {field}")
            
            # Validate parameters structure
            if 'parameters' in config:
                for param_name, param_config in config['parameters'].items():
                    if not isinstance(param_config, dict):
                        errors.append(f"Parameter {param_name} must be a dictionary")
                    elif 'type' not in param_config:
                        errors.append(f"Parameter {param_name} missing 'type' field")
                        
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in config.json: {e}")
        except Exception as e:
            errors.append(f"Error reading config.json: {e}")
        
        # Validate launcher.py
        if not self._validate_launcher(launcher_file):
            errors.append("Invalid launcher.py interface")
        
        return len(errors) == 0, errors
    
    def install_algorithm(self, source_path: str, algorithm_name: str = None) -> tuple[bool, str]:
        """
        Install an algorithm plugin from a source directory
        
        Args:
            source_path: Path to source algorithm directory
            algorithm_name: Optional name for the installed algorithm
            
        Returns:
            Tuple of (success, message)
        """
        source_dir = Path(source_path)
        
        # Validate source directory
        is_valid, errors = self.validate_algorithm_directory(source_dir)
        if not is_valid:
            return False, f"Invalid algorithm directory: {'; '.join(errors)}"
        
        # Determine target name
        if algorithm_name is None:
            try:
                with open(source_dir / "config.json", 'r') as f:
                    config = json.load(f)
                algorithm_name = config.get('name', source_dir.name).lower().replace(' ', '_')
            except:
                algorithm_name = source_dir.name
        
        # Create target directory
        target_dir = self.algorithms_dir / algorithm_name
        
        if target_dir.exists():
            return False, f"Algorithm {algorithm_name} already exists"
        
        try:
            # Copy algorithm files
            import shutil
            shutil.copytree(source_dir, target_dir)
            
            # Refresh algorithm discovery
            self.discover_algorithms()
            
            return True, f"Algorithm {algorithm_name} installed successfully"
            
        except Exception as e:
            return False, f"Error installing algorithm: {e}"
    
    def uninstall_algorithm(self, plugin_id: str) -> tuple[bool, str]:
        """
        Uninstall an algorithm plugin
        
        Args:
            plugin_id: The plugin identifier to uninstall
            
        Returns:
            Tuple of (success, message)
        """
        if plugin_id not in self.algorithm_configs:
            return False, f"Algorithm {plugin_id} not found"
        
        config = self.algorithm_configs[plugin_id]
        algorithm_dir = Path(config['plugin_path'])
        
        try:
            import shutil
            shutil.rmtree(algorithm_dir)
            
            # Remove from loaded algorithms
            if plugin_id in self.loaded_algorithms:
                del self.loaded_algorithms[plugin_id]
            
            del self.algorithm_configs[plugin_id]
            
            return True, f"Algorithm {plugin_id} uninstalled successfully"
            
        except Exception as e:
            return False, f"Error uninstalling algorithm: {e}"

# Global algorithm loader instance
algorithm_loader = AlgorithmLoader()

def get_algorithm_loader() -> AlgorithmLoader:
    """Get the global algorithm loader instance"""
    return algorithm_loader

def discover_algorithms() -> List[Dict[str, Any]]:
    """Convenience function to discover algorithms"""
    return algorithm_loader.discover_algorithms()

def load_algorithm(plugin_id: str, **kwargs) -> Optional[Any]:
    """Convenience function to load an algorithm"""
    return algorithm_loader.load_algorithm(plugin_id, **kwargs)