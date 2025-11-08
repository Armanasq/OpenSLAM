import sys
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from abc import ABC, abstractmethod
from collections import deque
import bisect
from datetime import datetime
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
class SensorData:
    def __init__(self, timestamp: float, data: Any, sensor_id: str, data_type: str):
        self.timestamp = timestamp
        self.data = data
        self.sensor_id = sensor_id
        self.data_type = data_type
        self.processed = False
class SensorBuffer:
    def __init__(self, max_size: int = 1000, max_time_window: float = 10.0):
        self.buffer = deque(maxlen=max_size)
        self.max_time_window = max_time_window
        self.timestamps = []
    def add_data(self, sensor_data: SensorData):
        self.buffer.append(sensor_data)
        bisect.insort(self.timestamps, sensor_data.timestamp)
        self._cleanup_old_data()
    def _cleanup_old_data(self):
        if not self.timestamps:
            return
        current_time = self.timestamps[-1]
        cutoff_time = current_time - self.max_time_window
        while self.buffer and self.buffer[0].timestamp < cutoff_time:
            removed_data = self.buffer.popleft()
            self.timestamps.remove(removed_data.timestamp)
    def get_data_at_time(self, timestamp: float, tolerance: float = 0.1) -> Optional[SensorData]:
        closest_idx = bisect.bisect_left(self.timestamps, timestamp)
        candidates = []
        for i in range(max(0, closest_idx - 1), min(len(self.timestamps), closest_idx + 2)):
            if i < len(self.buffer):
                data = list(self.buffer)[i]
                if abs(data.timestamp - timestamp) <= tolerance:
                    candidates.append((abs(data.timestamp - timestamp), data))
        if candidates:
            return min(candidates, key=lambda x: x[0])[1]
        return None
    def get_data_in_range(self, start_time: float, end_time: float) -> List[SensorData]:
        result = []
        for data in self.buffer:
            if start_time <= data.timestamp <= end_time:
                result.append(data)
        return sorted(result, key=lambda x: x.timestamp)
    def get_latest_data(self) -> Optional[SensorData]:
        return self.buffer[-1] if self.buffer else None
    def size(self) -> int:
        return len(self.buffer)
class MultiSensorSynchronizer:
    def __init__(self, sync_tolerance: float = 0.05, max_buffer_size: int = 1000):
        self.sensor_buffers = {}
        self.sync_tolerance = sync_tolerance
        self.max_buffer_size = max_buffer_size
        self.synchronized_data = deque(maxlen=max_buffer_size)
        self.sync_callbacks = []
    def register_sensor(self, sensor_id: str, data_type: str):
        self.sensor_buffers[sensor_id] = SensorBuffer(self.max_buffer_size)
    def add_sensor_data(self, sensor_id: str, timestamp: float, data: Any, data_type: str):
        if sensor_id not in self.sensor_buffers:
            self.register_sensor(sensor_id, data_type)
        sensor_data = SensorData(timestamp, data, sensor_id, data_type)
        self.sensor_buffers[sensor_id].add_data(sensor_data)
        self._attempt_synchronization(timestamp)
    def _attempt_synchronization(self, reference_timestamp: float):
        synchronized_frame = {}
        all_sensors_have_data = True
        for sensor_id, buffer in self.sensor_buffers.items():
            data = buffer.get_data_at_time(reference_timestamp, self.sync_tolerance)
            if data is not None:
                synchronized_frame[sensor_id] = data
            else:
                all_sensors_have_data = False
                break
        if all_sensors_have_data and len(synchronized_frame) > 1:
            sync_data = {'timestamp': reference_timestamp, 'sensors': synchronized_frame}
            self.synchronized_data.append(sync_data)
            for callback in self.sync_callbacks:
                callback(sync_data)
    def get_synchronized_data(self, start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[Dict]:
        if start_time is None and end_time is None:
            return list(self.synchronized_data)
        result = []
        for sync_data in self.synchronized_data:
            timestamp = sync_data['timestamp']
            if (start_time is None or timestamp >= start_time) and (end_time is None or timestamp <= end_time):
                result.append(sync_data)
        return result
    def register_sync_callback(self, callback: Callable[[Dict], None]):
        self.sync_callbacks.append(callback)
    def get_sync_statistics(self) -> Dict:
        total_frames = len(self.synchronized_data)
        if total_frames == 0:
            return {'total_synchronized_frames': 0, 'sync_rate': 0.0, 'average_time_diff': 0.0}
        time_diffs = []
        for sync_data in self.synchronized_data:
            timestamps = [data.timestamp for data in sync_data['sensors'].values()]
            if len(timestamps) > 1:
                time_diffs.append(max(timestamps) - min(timestamps))
        avg_time_diff = np.mean(time_diffs) if time_diffs else 0.0
        buffer_sizes = [buffer.size() for buffer in self.sensor_buffers.values()]
        total_data_points = sum(buffer_sizes)
        sync_rate = total_frames / total_data_points if total_data_points > 0 else 0.0
        return {'total_synchronized_frames': total_frames, 'sync_rate': sync_rate, 'average_time_diff': avg_time_diff, 'max_time_diff': max(time_diffs) if time_diffs else 0.0, 'buffer_sizes': dict(zip(self.sensor_buffers.keys(), buffer_sizes))}
class CoordinateTransformer:
    def __init__(self):
        self.transforms = {}
        self.transform_chain = {}
    def add_transform(self, from_frame: str, to_frame: str, transform_matrix: np.ndarray):
        if transform_matrix.shape != (4, 4):
            raise ValueError("Transform matrix must be 4x4")
        self.transforms[(from_frame, to_frame)] = transform_matrix
        self.transforms[(to_frame, from_frame)] = np.linalg.inv(transform_matrix)
        self._update_transform_chain()
    def _update_transform_chain(self):
        frames = set()
        for (from_frame, to_frame) in self.transforms.keys():
            frames.add(from_frame)
            frames.add(to_frame)
        self.transform_chain = {}
        for frame in frames:
            self.transform_chain[frame] = self._compute_transforms_from_frame(frame, frames)
    def _compute_transforms_from_frame(self, source_frame: str, all_frames: set) -> Dict[str, np.ndarray]:
        transforms = {source_frame: np.eye(4)}
        visited = {source_frame}
        queue = [source_frame]
        while queue:
            current_frame = queue.pop(0)
            current_transform = transforms[current_frame]
            for (from_frame, to_frame), transform in self.transforms.items():
                if from_frame == current_frame and to_frame not in visited:
                    transforms[to_frame] = current_transform @ transform
                    visited.add(to_frame)
                    queue.append(to_frame)
        return transforms
    def transform_points(self, points: np.ndarray, from_frame: str, to_frame: str) -> np.ndarray:
        if from_frame == to_frame:
            return points
        if from_frame not in self.transform_chain:
            raise ValueError(f"Unknown source frame: {from_frame}")
        if to_frame not in self.transform_chain[from_frame]:
            raise ValueError(f"No transform path from {from_frame} to {to_frame}")
        transform = self.transform_chain[from_frame][to_frame]
        if points.shape[1] == 3:
            points_homo = np.hstack([points, np.ones((points.shape[0], 1))])
        else:
            points_homo = points
        transformed = (transform @ points_homo.T).T
        return transformed[:, :3]
    def transform_pose(self, pose_matrix: np.ndarray, from_frame: str, to_frame: str) -> np.ndarray:
        if from_frame == to_frame:
            return pose_matrix
        if from_frame not in self.transform_chain:
            raise ValueError(f"Unknown source frame: {from_frame}")
        if to_frame not in self.transform_chain[from_frame]:
            raise ValueError(f"No transform path from {from_frame} to {to_frame}")
        transform = self.transform_chain[from_frame][to_frame]
        return transform @ pose_matrix
    def get_transform(self, from_frame: str, to_frame: str) -> np.ndarray:
        if from_frame == to_frame:
            return np.eye(4)
        if from_frame not in self.transform_chain:
            raise ValueError(f"Unknown source frame: {from_frame}")
        if to_frame not in self.transform_chain[from_frame]:
            raise ValueError(f"No transform path from {from_frame} to {to_frame}")
        return self.transform_chain[from_frame][to_frame]
    def list_frames(self) -> List[str]:
        return list(self.transform_chain.keys())
class CalibrationValidator:
    @staticmethod
    def validate_camera_matrix(K: np.ndarray, image_size: Tuple[int, int]) -> Dict:
        if K.shape != (3, 3):
            return {'valid': False, 'errors': ['Camera matrix must be 3x3']}
        errors = []
        fx, fy = K[0, 0], K[1, 1]
        cx, cy = K[0, 2], K[1, 2]
        width, height = image_size
        if fx <= 0 or fy <= 0:
            errors.append('Focal lengths must be positive')
        if not (0 <= cx <= width):
            errors.append(f'Principal point cx ({cx}) outside image width ({width})')
        if not (0 <= cy <= height):
            errors.append(f'Principal point cy ({cy}) outside image height ({height})')
        if abs(fx - fy) / max(fx, fy) > 0.1:
            errors.append('Focal lengths differ significantly (non-square pixels)')
        if K[0, 1] != 0 or K[1, 0] != 0 or K[2, 0] != 0 or K[2, 1] != 0 or K[2, 2] != 1:
            errors.append('Camera matrix has invalid structure')
        return {'valid': len(errors) == 0, 'errors': errors, 'focal_length': (fx + fy) / 2, 'principal_point': (cx, cy), 'aspect_ratio': fx / fy}
    @staticmethod
    def validate_stereo_calibration(K1: np.ndarray, K2: np.ndarray, R: np.ndarray, t: np.ndarray, image_size: Tuple[int, int]) -> Dict:
        errors = []
        cam1_validation = CalibrationValidator.validate_camera_matrix(K1, image_size)
        cam2_validation = CalibrationValidator.validate_camera_matrix(K2, image_size)
        if not cam1_validation['valid']:
            errors.extend([f"Camera 1: {err}" for err in cam1_validation['errors']])
        if not cam2_validation['valid']:
            errors.extend([f"Camera 2: {err}" for err in cam2_validation['errors']])
        if R.shape != (3, 3):
            errors.append('Rotation matrix must be 3x3')
        else:
            det_R = np.linalg.det(R)
            if abs(det_R - 1.0) > 1e-6:
                errors.append(f'Rotation matrix determinant ({det_R}) should be 1.0')
            should_be_identity = R @ R.T
            identity_error = np.max(np.abs(should_be_identity - np.eye(3)))
            if identity_error > 1e-6:
                errors.append(f'Rotation matrix not orthogonal (error: {identity_error})')
        if t.shape not in [(3,), (3, 1)]:
            errors.append('Translation vector must be 3x1 or (3,)')
        else:
            baseline = np.linalg.norm(t)
            if baseline < 0.01:
                errors.append(f'Baseline too small ({baseline}m)')
            elif baseline > 2.0:
                errors.append(f'Baseline unusually large ({baseline}m)')
        rotation_angle = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
        return {'valid': len(errors) == 0, 'errors': errors, 'baseline': np.linalg.norm(t), 'rotation_angle_deg': np.degrees(rotation_angle), 'focal_length_diff': abs(K1[0, 0] - K2[0, 0])}
    @staticmethod
    def validate_lidar_camera_transform(transform: np.ndarray, expected_rotation_axis: Optional[np.ndarray] = None) -> Dict:
        if transform.shape != (4, 4):
            return {'valid': False, 'errors': ['Transform must be 4x4 matrix']}
        errors = []
        R = transform[:3, :3]
        t = transform[:3, 3]
        det_R = np.linalg.det(R)
        if abs(det_R - 1.0) > 1e-6:
            errors.append(f'Rotation part determinant ({det_R}) should be 1.0')
        should_be_identity = R @ R.T
        identity_error = np.max(np.abs(should_be_identity - np.eye(3)))
        if identity_error > 1e-6:
            errors.append(f'Rotation part not orthogonal (error: {identity_error})')
        if transform[3, 0] != 0 or transform[3, 1] != 0 or transform[3, 2] != 0 or transform[3, 3] != 1:
            errors.append('Bottom row should be [0, 0, 0, 1]')
        translation_magnitude = np.linalg.norm(t)
        if translation_magnitude > 5.0:
            errors.append(f'Translation magnitude unusually large ({translation_magnitude}m)')
        rotation_angle = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
        return {'valid': len(errors) == 0, 'errors': errors, 'translation_magnitude': translation_magnitude, 'rotation_angle_deg': np.degrees(rotation_angle)}
class CalibrationCorrector:
    @staticmethod
    def correct_camera_matrix(K: np.ndarray, image_size: Tuple[int, int]) -> np.ndarray:
        K_corrected = K.copy()
        width, height = image_size
        if K_corrected[0, 0] <= 0:
            K_corrected[0, 0] = width * 0.7
        if K_corrected[1, 1] <= 0:
            K_corrected[1, 1] = height * 0.7
        if not (0 <= K_corrected[0, 2] <= width):
            K_corrected[0, 2] = width / 2
        if not (0 <= K_corrected[1, 2] <= height):
            K_corrected[1, 2] = height / 2
        K_corrected[0, 1] = 0
        K_corrected[1, 0] = 0
        K_corrected[2, 0] = 0
        K_corrected[2, 1] = 0
        K_corrected[2, 2] = 1
        return K_corrected
    @staticmethod
    def orthogonalize_rotation_matrix(R: np.ndarray) -> np.ndarray:
        U, S, Vt = np.linalg.svd(R)
        R_orthogonal = U @ Vt
        if np.linalg.det(R_orthogonal) < 0:
            Vt[-1, :] *= -1
            R_orthogonal = U @ Vt
        return R_orthogonal
    @staticmethod
    def normalize_transform_matrix(T: np.ndarray) -> np.ndarray:
        T_corrected = T.copy()
        R = T_corrected[:3, :3]
        R_orthogonal = CalibrationCorrector.orthogonalize_rotation_matrix(R)
        T_corrected[:3, :3] = R_orthogonal
        T_corrected[3, :3] = 0
        T_corrected[3, 3] = 1
        return T_corrected
class TimestampAligner:
    def __init__(self, reference_sensor: str):
        self.reference_sensor = reference_sensor
        self.time_offsets = {}
        self.drift_rates = {}
    def estimate_time_offset(self, sensor_id: str, sensor_timestamps: np.ndarray, reference_timestamps: np.ndarray) -> float:
        if len(sensor_timestamps) != len(reference_timestamps):
            min_len = min(len(sensor_timestamps), len(reference_timestamps))
            sensor_timestamps = sensor_timestamps[:min_len]
            reference_timestamps = reference_timestamps[:min_len]
        time_diffs = sensor_timestamps - reference_timestamps
        offset = np.median(time_diffs)
        self.time_offsets[sensor_id] = offset
        if len(time_diffs) > 1:
            drift_rate = np.polyfit(reference_timestamps, time_diffs, 1)[0]
            self.drift_rates[sensor_id] = drift_rate
        else:
            self.drift_rates[sensor_id] = 0.0
        return offset
    def align_timestamp(self, sensor_id: str, timestamp: float, reference_time: float = None) -> float:
        if sensor_id not in self.time_offsets:
            return timestamp
        offset = self.time_offsets[sensor_id]
        drift_rate = self.drift_rates.get(sensor_id, 0.0)
        if reference_time is not None:
            drift_correction = drift_rate * (reference_time - timestamp)
            return timestamp - offset - drift_correction
        else:
            return timestamp - offset
    def get_alignment_statistics(self) -> Dict:
        return {'time_offsets': self.time_offsets.copy(), 'drift_rates': self.drift_rates.copy(), 'reference_sensor': self.reference_sensor}