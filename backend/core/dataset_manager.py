import os
import sys
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from shared.models import Dataset
from config.settings import DATA_DIR
class ValidationError(Exception):
    def __init__(self, message: str, errors: List[str]):
        self.message = message
        self.errors = errors
        super().__init__(message)
class DatasetManager:
    def __init__(self, data_root: str = DATA_DIR):
        self.data_root = data_root
        self.datasets = {}
    def validate_kitti_format(self, dataset_path: str) -> Tuple[bool, List[str]]:
        errors = []
        if not os.path.exists(dataset_path):
            errors.append(f"Dataset path does not exist: {dataset_path}")
            return False, errors
        if not os.path.isdir(dataset_path):
            errors.append(f"Dataset path is not a directory: {dataset_path}")
            return False, errors
        required_files = ["calib.txt", "times.txt"]
        for req_file in required_files:
            file_path = os.path.join(dataset_path, req_file)
            if not os.path.exists(file_path):
                errors.append(f"Missing required file: {req_file}")
            elif not os.path.isfile(file_path):
                errors.append(f"Required file is not a file: {req_file}")
        sensor_dirs = ["image_0", "image_1", "image_2", "image_3", "velodyne"]
        available_sensors = []
        for sensor_dir in sensor_dirs:
            sensor_path = os.path.join(dataset_path, sensor_dir)
            if os.path.exists(sensor_path):
                if os.path.isdir(sensor_path):
                    files = [f for f in os.listdir(sensor_path) if f.endswith(('.png', '.jpg', '.bin'))]
                    if files:
                        available_sensors.append(sensor_dir)
                else:
                    errors.append(f"Sensor directory is not a directory: {sensor_dir}")
        if not available_sensors:
            errors.append("No valid sensor directories found (image_0, image_1, image_2, image_3, velodyne)")
        if os.path.exists(os.path.join(dataset_path, "calib.txt")):
            calib_errors = self._validate_calibration_file(os.path.join(dataset_path, "calib.txt"))
            errors.extend(calib_errors)
        if os.path.exists(os.path.join(dataset_path, "times.txt")):
            times_errors = self._validate_times_file(os.path.join(dataset_path, "times.txt"))
            errors.extend(times_errors)
        pose_files = ["pose.txt", "poses.txt"]
        for pose_file_name in pose_files:
            pose_file = os.path.join(dataset_path, pose_file_name)
            if os.path.exists(pose_file):
                pose_errors = self._validate_pose_file(pose_file)
                errors.extend(pose_errors)
                break
        sequence_lengths = {}
        for sensor in available_sensors:
            length = self._get_sequence_length(dataset_path, sensor)
            sequence_lengths[sensor] = length
        if len(set(sequence_lengths.values())) > 1:
            errors.append(f"Inconsistent sequence lengths across sensors: {sequence_lengths}")
        return len(errors) == 0, errors
    def _validate_calibration_file(self, calib_path: str) -> List[str]:
        errors = []
        try:
            with open(calib_path, 'r') as f:
                lines = f.readlines()
            required_keys = ["P0", "P1", "P2", "P3", "Tr"]
            found_keys = set()
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                if ':' not in line:
                    errors.append(f"Invalid calibration format at line {line_num}: missing colon")
                    continue
                key, values_str = line.split(':', 1)
                key = key.strip()
                found_keys.add(key)
                try:
                    values = [float(x) for x in values_str.split()]
                    if key in ["P0", "P1", "P2", "P3"] and len(values) != 12:
                        errors.append(f"Projection matrix {key} should have 12 values, got {len(values)}")
                    elif key == "Tr" and len(values) != 12:
                        errors.append(f"Transformation matrix Tr should have 12 values, got {len(values)}")
                except ValueError:
                    errors.append(f"Invalid numeric values in calibration line {line_num}")
            missing_keys = set(required_keys) - found_keys
            if missing_keys:
                errors.append(f"Missing calibration keys: {list(missing_keys)}")
        except Exception as e:
            errors.append(f"Error reading calibration file: {str(e)}")
        return errors
    def _validate_times_file(self, times_path: str) -> List[str]:
        errors = []
        try:
            with open(times_path, 'r') as f:
                lines = f.readlines()
            prev_time = -1.0
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    timestamp = float(line)
                    if timestamp < prev_time:
                        errors.append(f"Non-monotonic timestamp at line {line_num}: {timestamp}")
                    prev_time = timestamp
                except ValueError:
                    errors.append(f"Invalid timestamp format at line {line_num}: {line}")
        except Exception as e:
            errors.append(f"Error reading times file: {str(e)}")
        return errors
    def _validate_pose_file(self, pose_path: str) -> List[str]:
        errors = []
        try:
            with open(pose_path, 'r') as f:
                lines = f.readlines()
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    values = [float(x) for x in line.split()]
                    if len(values) != 12:
                        errors.append(f"Pose at line {line_num} should have 12 values, got {len(values)}")
                except ValueError:
                    errors.append(f"Invalid pose format at line {line_num}")
        except Exception as e:
            errors.append(f"Error reading pose file: {str(e)}")
        return errors
    def load_kitti_dataset(self, dataset_path: str) -> Dataset:
        is_valid, validation_errors = self.validate_kitti_format(dataset_path)
        if not is_valid:
            raise ValidationError("KITTI dataset validation failed", validation_errors)
        sensor_dirs = ["image_0", "image_1", "image_2", "image_3", "velodyne"]
        available_sensors = []
        for sensor_dir in sensor_dirs:
            if os.path.exists(os.path.join(dataset_path, sensor_dir)):
                available_sensors.append(sensor_dir)
        sequence_length = self._get_sequence_length(dataset_path, available_sensors[0])
        calibration = self._load_calibration(os.path.join(dataset_path, "calib.txt"))
        metadata = self._extract_metadata(dataset_path, available_sensors)
        dataset_id = os.path.basename(dataset_path)
        file_paths = {"root": dataset_path, "calib": os.path.join(dataset_path, "calib.txt"), "times": os.path.join(dataset_path, "times.txt")}
        pose_files = ["poses.txt", "pose.txt"]
        for pose_file_name in pose_files:
            pose_file_path = os.path.join(dataset_path, pose_file_name)
            if os.path.exists(pose_file_path):
                file_paths["poses"] = pose_file_path
                break
        for sensor in available_sensors:
            file_paths[sensor] = os.path.join(dataset_path, sensor)
        dataset = Dataset(id=dataset_id, name=f"KITTI_{dataset_id}", format="KITTI", sequence_length=sequence_length, sensors=available_sensors, calibration=calibration, metadata=metadata, created_at=datetime.now(), file_paths=file_paths)
        self.datasets[dataset_id] = dataset
        return dataset
    def _extract_metadata(self, dataset_path: str, sensors: List[str]) -> Dict:
        metadata = {"path": dataset_path, "sensors": {}}
        for sensor in sensors:
            sensor_path = os.path.join(dataset_path, sensor)
            files = [f for f in os.listdir(sensor_path) if f.endswith(('.png', '.jpg', '.bin'))]
            if sensor.startswith("image"):
                metadata["sensors"][sensor] = {"type": "camera", "format": "grayscale" if sensor in ["image_0", "image_1"] else "color", "count": len(files)}
            elif sensor == "velodyne":
                metadata["sensors"][sensor] = {"type": "lidar", "format": "binary", "count": len(files)}
        pose_files = ["poses.txt", "pose.txt"]
        metadata["has_ground_truth"] = any(os.path.exists(os.path.join(dataset_path, pf)) for pf in pose_files)
        return metadata
    def _get_sequence_length(self, dataset_path: str, sensor_dir: str) -> int:
        sensor_path = os.path.join(dataset_path, sensor_dir)
        if os.path.exists(sensor_path):
            files = [f for f in os.listdir(sensor_path) if f.endswith(('.png', '.jpg', '.bin'))]
            return len(files)
        return 0
    def _load_calibration(self, calib_path: str) -> Dict:
        calib_data = {}
        with open(calib_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    key, values = line.split(':', 1)
                    calib_data[key.strip()] = [float(x) for x in values.split()]
        return calib_data
    def load_frame_data(self, dataset_id: str, frame_idx: int) -> Optional[Dict]:
        dataset = self.get_dataset(dataset_id)
        if not dataset or frame_idx >= dataset.sequence_length:
            return None
        frame_data = {"frame_id": frame_idx, "timestamp": None}
        times_path = dataset.file_paths.get("times")
        if times_path and os.path.exists(times_path):
            with open(times_path, 'r') as f:
                lines = f.readlines()
                if frame_idx < len(lines):
                    frame_data["timestamp"] = float(lines[frame_idx].strip())
        for sensor in dataset.sensors:
            sensor_path = dataset.file_paths[sensor]
            if sensor.startswith("image"):
                img_file = os.path.join(sensor_path, f"{frame_idx:06d}.png")
                if os.path.exists(img_file):
                    frame_data[sensor] = img_file
            elif sensor == "velodyne":
                lidar_file = os.path.join(sensor_path, f"{frame_idx:06d}.bin")
                if os.path.exists(lidar_file):
                    frame_data[sensor] = lidar_file
        poses_path = dataset.file_paths.get("poses")
        if poses_path and os.path.exists(poses_path):
            with open(poses_path, 'r') as f:
                lines = f.readlines()
                if frame_idx < len(lines):
                    pose_values = [float(x) for x in lines[frame_idx].split()]
                    pose_matrix = np.array(pose_values).reshape(3, 4)
                    frame_data["ground_truth_pose"] = pose_matrix
        return frame_data
    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        return self.datasets.get(dataset_id)
    def list_datasets(self) -> List[Dataset]:
        return list(self.datasets.values())
    def load_frame_range(self, dataset_id: str, start_frame: int, end_frame: int) -> List[Dict]:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return []
        frames = []
        for frame_idx in range(start_frame, min(end_frame, dataset.sequence_length)):
            frame_data = self.load_frame_data(dataset_id, frame_idx)
            if frame_data:
                frames.append(frame_data)
        return frames
    def get_sensor_data_path(self, dataset_id: str, sensor: str, frame_idx: int) -> Optional[str]:
        dataset = self.get_dataset(dataset_id)
        if not dataset or sensor not in dataset.sensors:
            return None
        sensor_path = dataset.file_paths[sensor]
        if sensor.startswith("image"):
            return os.path.join(sensor_path, f"{frame_idx:06d}.png")
        elif sensor == "velodyne":
            return os.path.join(sensor_path, f"{frame_idx:06d}.bin")
        return None
    def load_lidar_data(self, dataset_id: str, frame_idx: int) -> Optional[np.ndarray]:
        lidar_path = self.get_sensor_data_path(dataset_id, "velodyne", frame_idx)
        if lidar_path and os.path.exists(lidar_path):
            return np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        return None
    def transform_coordinates(self, dataset_id: str, points: np.ndarray, from_frame: str, to_frame: str) -> np.ndarray:
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        calibration = dataset.calibration
        if from_frame == "lidar" and to_frame == "camera":
            if "Tr" in calibration:
                tr_matrix = np.array(calibration["Tr"]).reshape(3, 4)
                if points.shape[1] == 3:
                    points_homo = np.hstack([points, np.ones((points.shape[0], 1))])
                else:
                    points_homo = points
                transformed = (tr_matrix @ points_homo.T).T
                return transformed
        elif from_frame == "camera" and to_frame == "lidar":
            if "Tr" in calibration:
                tr_matrix = np.array(calibration["Tr"]).reshape(3, 4)
                R = tr_matrix[:3, :3]
                t = tr_matrix[:3, 3]
                R_inv = R.T
                t_inv = -R_inv @ t
                if points.shape[1] == 3:
                    transformed = (R_inv @ points.T).T + t_inv
                    return transformed
        return points