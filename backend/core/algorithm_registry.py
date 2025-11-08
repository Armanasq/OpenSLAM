import sys
import inspect
from typing import Dict, List, Type, Optional, Any, Tuple
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from backend.core.algorithm_interface import SLAMAlgorithm, VisualOdometry, LiDARSLAM
class AlgorithmValidationError(Exception):
    def __init__(self, message: str, errors: List[str]):
        self.message = message
        self.errors = errors
        super().__init__(message)
class AlgorithmRegistry:
    def __init__(self):
        self.algorithms = {}
        self.templates = {}
        self._initialize_templates()
    def _initialize_templates(self):
        self.templates['visual_odometry'] = {'base_class': VisualOdometry, 'required_methods': ['detect_features', 'match_features', 'estimate_motion'], 'optional_methods': ['initialize', 'process_frame'], 'parameters': {'feature_detector_type': 'ORB', 'max_features': 1000, 'match_threshold': 0.7}}
        self.templates['lidar_slam'] = {'base_class': LiDARSLAM, 'required_methods': ['preprocess_scan', 'match_scans', 'update_map'], 'optional_methods': ['initialize', 'process_frame'], 'parameters': {'voxel_size': 0.1, 'max_range': 100.0, 'min_range': 1.0}}
        self.templates['slam_algorithm'] = {'base_class': SLAMAlgorithm, 'required_methods': ['initialize', 'process_frame', 'get_current_pose', 'get_trajectory', 'reset'], 'optional_methods': [], 'parameters': {'max_iterations': 100, 'convergence_threshold': 1e-6}}
    def validate_algorithm(self, algorithm_class: Type[SLAMAlgorithm]) -> Tuple[bool, List[str]]:
        errors = []
        if not issubclass(algorithm_class, SLAMAlgorithm):
            errors.append("Algorithm must inherit from SLAMAlgorithm")
            return False, errors
        template_name = self._get_template_name(algorithm_class)
        if template_name not in self.templates:
            errors.append(f"No template found for algorithm type: {template_name}")
            return False, errors
        template = self.templates[template_name]
        required_methods = template['required_methods']
        for method_name in required_methods:
            if not hasattr(algorithm_class, method_name):
                errors.append(f"Missing required method: {method_name}")
            else:
                method = getattr(algorithm_class, method_name)
                if not callable(method):
                    errors.append(f"Method {method_name} is not callable")
                elif method_name in ['initialize', 'process_frame', 'get_current_pose', 'get_trajectory', 'reset']:
                    if getattr(method, '__isabstractmethod__', False):
                        errors.append(f"Abstract method {method_name} not implemented")
        try:
            sig = inspect.signature(algorithm_class.__init__)
            params = list(sig.parameters.keys())
            if 'algorithm_id' not in params or 'name' not in params:
                errors.append("Constructor must accept algorithm_id and name parameters")
        except Exception as e:
            errors.append(f"Error inspecting constructor: {str(e)}")
        return len(errors) == 0, errors
    def _get_template_name(self, algorithm_class: Type[SLAMAlgorithm]) -> str:
        if issubclass(algorithm_class, VisualOdometry):
            return 'visual_odometry'
        elif issubclass(algorithm_class, LiDARSLAM):
            return 'lidar_slam'
        else:
            return 'slam_algorithm'
    def register_algorithm(self, algorithm_class: Type[SLAMAlgorithm], algorithm_id: str) -> bool:
        is_valid, validation_errors = self.validate_algorithm(algorithm_class)
        if not is_valid:
            raise AlgorithmValidationError(f"Algorithm validation failed for {algorithm_id}", validation_errors)
        self.algorithms[algorithm_id] = {'class': algorithm_class, 'template': self._get_template_name(algorithm_class), 'registered_at': __import__('datetime').datetime.now()}
        return True
    def get_algorithm(self, algorithm_id: str) -> Optional[Type[SLAMAlgorithm]]:
        if algorithm_id in self.algorithms:
            return self.algorithms[algorithm_id]['class']
        return None
    def create_algorithm_instance(self, algorithm_id: str, name: str, parameters: Optional[Dict] = None) -> Optional[SLAMAlgorithm]:
        algorithm_class = self.get_algorithm(algorithm_id)
        if not algorithm_class:
            return None
        try:
            instance = algorithm_class(algorithm_id, name)
            if parameters:
                instance.set_parameters(parameters)
            return instance
        except Exception:
            return None
    def list_algorithms(self) -> List[Dict]:
        result = []
        for alg_id, alg_info in self.algorithms.items():
            result.append({'id': alg_id, 'class_name': alg_info['class'].__name__, 'template': alg_info['template'], 'registered_at': alg_info['registered_at']})
        return result
    def get_template(self, template_name: str) -> Optional[Dict]:
        return self.templates.get(template_name)
    def list_templates(self) -> List[str]:
        return list(self.templates.keys())
    def unregister_algorithm(self, algorithm_id: str) -> bool:
        if algorithm_id in self.algorithms:
            del self.algorithms[algorithm_id]
            return True
        return False
class AlgorithmTemplate:
    def __init__(self, template_name: str, registry: AlgorithmRegistry):
        self.template_name = template_name
        self.registry = registry
        self.template_info = registry.get_template(template_name)
    def generate_skeleton_code(self) -> str:
        if not self.template_info:
            return ""
        base_class = self.template_info['base_class']
        required_methods = self.template_info['required_methods']
        class_name = f"My{base_class.__name__}"
        code_lines = [f"class {class_name}({base_class.__name__}):", f"    def __init__(self, algorithm_id: str, name: str):", f"        super().__init__(algorithm_id, name)"]
        for method_name in required_methods:
            if hasattr(base_class, method_name):
                method = getattr(base_class, method_name)
                try:
                    sig = inspect.signature(method)
                    params = ', '.join([param.name for param in sig.parameters.values() if param.name != 'self'])
                    code_lines.append(f"    def {method_name}(self, {params}):")
                    code_lines.append(f"        pass")
                except Exception:
                    code_lines.append(f"    def {method_name}(self):")
                    code_lines.append(f"        pass")
        return '\n'.join(code_lines)
    def get_method_signatures(self) -> Dict[str, str]:
        if not self.template_info:
            return {}
        base_class = self.template_info['base_class']
        signatures = {}
        for method_name in self.template_info['required_methods']:
            if hasattr(base_class, method_name):
                method = getattr(base_class, method_name)
                try:
                    sig = inspect.signature(method)
                    signatures[method_name] = str(sig)
                except Exception:
                    signatures[method_name] = "Signature unavailable"
        return signatures
    def get_default_parameters(self) -> Dict:
        if not self.template_info:
            return {}
        return self.template_info.get('parameters', {}).copy()