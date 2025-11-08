import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from shared.models import TrajectoryPoint, PerformanceMetrics
class SLAMAlgorithm(ABC):
    def __init__(self, algorithm_id: str, name: str):
        self.algorithm_id = algorithm_id
        self.name = name
        self.is_initialized = False
        self.current_pose = np.eye(4)
        self.trajectory = []
        self.landmarks = []
        self.performance_metrics = {}
    @abstractmethod
    def initialize(self, calibration: Dict, initial_pose: Optional[np.ndarray] = None) -> bool:
        pass
    @abstractmethod
    def process_frame(self, frame_data: Dict) -> Dict:
        pass
    @abstractmethod
    def get_current_pose(self) -> np.ndarray:
        pass
    @abstractmethod
    def get_trajectory(self) -> List[TrajectoryPoint]:
        pass
    @abstractmethod
    def reset(self) -> None:
        pass
    def get_landmarks(self) -> List[np.ndarray]:
        return self.landmarks
    def get_performance_metrics(self) -> Dict:
        return self.performance_metrics
    def set_parameters(self, parameters: Dict) -> None:
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
class VisualOdometry(SLAMAlgorithm):
    def __init__(self, algorithm_id: str, name: str):
        super().__init__(algorithm_id, name)
        self.feature_detector = None
        self.feature_matcher = None
        self.motion_estimator = None
        self.previous_frame = None
        self.previous_keypoints = None
        self.previous_descriptors = None
    @abstractmethod
    def detect_features(self, image: np.ndarray) -> Tuple[List, np.ndarray]:
        pass
    @abstractmethod
    def match_features(self, desc1: np.ndarray, desc2: np.ndarray) -> List[Tuple[int, int]]:
        pass
    @abstractmethod
    def estimate_motion(self, kp1: List, kp2: List, matches: List, calibration: Dict) -> np.ndarray:
        pass
    def process_frame(self, frame_data: Dict) -> Dict:
        if 'image_0' not in frame_data:
            return {'success': False, 'error': 'No image data'}
        image_path = frame_data['image_0']
        image = self._load_image(image_path)
        keypoints, descriptors = self.detect_features(image)
        result = {'success': True, 'keypoints_count': len(keypoints), 'pose': self.current_pose.copy()}
        if self.previous_descriptors is not None:
            matches = self.match_features(self.previous_descriptors, descriptors)
            if len(matches) > 8:
                motion = self.estimate_motion(self.previous_keypoints, keypoints, matches, frame_data.get('calibration', {}))
                self.current_pose = self.current_pose @ motion
                trajectory_point = TrajectoryPoint(position=(self.current_pose[0, 3], self.current_pose[1, 3], self.current_pose[2, 3]), orientation=(0.0, 0.0, 0.0, 1.0), timestamp=frame_data.get('timestamp', 0.0), frame_id=frame_data.get('frame_id', 0))
                self.trajectory.append(trajectory_point)
                result['matches_count'] = len(matches)
                result['motion'] = motion
        self.previous_frame = image
        self.previous_keypoints = keypoints
        self.previous_descriptors = descriptors
        return result
    def _load_image(self, image_path: str) -> np.ndarray:
        import cv2
        return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    def get_current_pose(self) -> np.ndarray:
        return self.current_pose.copy()
    def get_trajectory(self) -> List[TrajectoryPoint]:
        return self.trajectory.copy()
    def reset(self) -> None:
        self.current_pose = np.eye(4)
        self.trajectory = []
        self.previous_frame = None
        self.previous_keypoints = None
        self.previous_descriptors = None
        self.is_initialized = False
class LiDARSLAM(SLAMAlgorithm):
    def __init__(self, algorithm_id: str, name: str):
        super().__init__(algorithm_id, name)
        self.scan_matcher = None
        self.previous_scan = None
        self.map_points = []
    @abstractmethod
    def preprocess_scan(self, lidar_data: np.ndarray) -> np.ndarray:
        pass
    @abstractmethod
    def match_scans(self, scan1: np.ndarray, scan2: np.ndarray) -> np.ndarray:
        pass
    @abstractmethod
    def update_map(self, scan: np.ndarray, pose: np.ndarray) -> None:
        pass
    def process_frame(self, frame_data: Dict) -> Dict:
        if 'velodyne' not in frame_data:
            return {'success': False, 'error': 'No LiDAR data'}
        lidar_path = frame_data['velodyne']
        lidar_data = self._load_lidar_data(lidar_path)
        processed_scan = self.preprocess_scan(lidar_data)
        result = {'success': True, 'points_count': len(processed_scan), 'pose': self.current_pose.copy()}
        if self.previous_scan is not None:
            motion = self.match_scans(self.previous_scan, processed_scan)
            self.current_pose = self.current_pose @ motion
            self.update_map(processed_scan, self.current_pose)
            trajectory_point = TrajectoryPoint(position=(self.current_pose[0, 3], self.current_pose[1, 3], self.current_pose[2, 3]), orientation=(0.0, 0.0, 0.0, 1.0), timestamp=frame_data.get('timestamp', 0.0), frame_id=frame_data.get('frame_id', 0))
            self.trajectory.append(trajectory_point)
            result['motion'] = motion
        self.previous_scan = processed_scan
        return result
    def _load_lidar_data(self, lidar_path: str) -> np.ndarray:
        return np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    def get_current_pose(self) -> np.ndarray:
        return self.current_pose.copy()
    def get_trajectory(self) -> List[TrajectoryPoint]:
        return self.trajectory.copy()
    def get_map_points(self) -> List[np.ndarray]:
        return self.map_points.copy()
    def reset(self) -> None:
        self.current_pose = np.eye(4)
        self.trajectory = []
        self.previous_scan = None
        self.map_points = []
        self.is_initialized = False