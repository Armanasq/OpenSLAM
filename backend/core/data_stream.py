import asyncio
import sys
import numpy as np
from typing import Dict, List, Optional, Tuple, AsyncGenerator
from datetime import datetime
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from backend.core.dataset_manager import DatasetManager
class DataStream:
    def __init__(self, dataset_manager: DatasetManager, dataset_id: str, frame_range: Optional[Tuple[int, int]] = None):
        self.dataset_manager = dataset_manager
        self.dataset_id = dataset_id
        self.dataset = dataset_manager.get_dataset(dataset_id)
        if not self.dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        if frame_range:
            start, end = frame_range
            self.start_frame = max(0, start)
            self.end_frame = min(self.dataset.sequence_length, end)
        else:
            self.start_frame = 0
            self.end_frame = self.dataset.sequence_length
        self.current_frame = self.start_frame
    async def next_frame(self) -> Optional[Dict]:
        if self.current_frame >= self.end_frame:
            return None
        frame_data = self.dataset_manager.load_frame_data(self.dataset_id, self.current_frame)
        self.current_frame += 1
        return frame_data
    async def stream_frames(self) -> AsyncGenerator[Dict, None]:
        while self.current_frame < self.end_frame:
            frame_data = await self.next_frame()
            if frame_data:
                yield frame_data
    def reset(self):
        self.current_frame = self.start_frame
    def seek(self, frame_idx: int):
        if self.start_frame <= frame_idx < self.end_frame:
            self.current_frame = frame_idx
    def get_frame_count(self) -> int:
        return self.end_frame - self.start_frame
    def get_progress(self) -> float:
        total_frames = self.get_frame_count()
        if total_frames == 0:
            return 1.0
        processed_frames = self.current_frame - self.start_frame
        return processed_frames / total_frames
class DataPreprocessor:
    def __init__(self, dataset_manager: DatasetManager):
        self.dataset_manager = dataset_manager
    def align_coordinate_systems(self, dataset_id: str) -> Dict:
        dataset = self.dataset_manager.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        calibration = dataset.calibration
        transforms = {}
        if "Tr" in calibration:
            tr_values = calibration["Tr"]
            tr_matrix = np.array(tr_values).reshape(3, 4)
            transforms["lidar_to_camera"] = tr_matrix
            transforms["camera_to_lidar"] = self._invert_transform(tr_matrix)
        projection_matrices = {}
        for key in ["P0", "P1", "P2", "P3"]:
            if key in calibration:
                p_values = calibration[key]
                projection_matrices[key] = np.array(p_values).reshape(3, 4)
        transforms["projection_matrices"] = projection_matrices
        return transforms
    def _invert_transform(self, transform_matrix: np.ndarray) -> np.ndarray:
        R = transform_matrix[:3, :3]
        t = transform_matrix[:3, 3]
        R_inv = R.T
        t_inv = -R_inv @ t
        inv_transform = np.zeros((3, 4))
        inv_transform[:3, :3] = R_inv
        inv_transform[:3, 3] = t_inv
        return inv_transform
    def load_calibration_matrices(self, dataset_id: str) -> Dict[str, np.ndarray]:
        dataset = self.dataset_manager.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        calibration = dataset.calibration
        matrices = {}
        for key, values in calibration.items():
            if key in ["P0", "P1", "P2", "P3"]:
                matrices[key] = np.array(values).reshape(3, 4)
            elif key == "Tr":
                matrices[key] = np.array(values).reshape(3, 4)
        return matrices
    def extract_camera_intrinsics(self, dataset_id: str) -> Dict[str, np.ndarray]:
        matrices = self.load_calibration_matrices(dataset_id)
        intrinsics = {}
        for key in ["P0", "P1", "P2", "P3"]:
            if key in matrices:
                P = matrices[key]
                K = P[:3, :3]
                intrinsics[key] = K
        return intrinsics
    def create_subset(self, dataset_id: str, frame_indices: List[int]) -> DataStream:
        if not frame_indices:
            raise ValueError("Frame indices list cannot be empty")
        min_idx = min(frame_indices)
        max_idx = max(frame_indices)
        return DataStream(self.dataset_manager, dataset_id, (min_idx, max_idx + 1))
    def validate_frame_range(self, dataset_id: str, frame_range: Tuple[int, int]) -> bool:
        dataset = self.dataset_manager.get_dataset(dataset_id)
        if not dataset:
            return False
        start, end = frame_range
        return 0 <= start < end <= dataset.sequence_length