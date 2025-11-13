import numpy as np
import json
from pathlib import Path

class LiveVisualizer:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.trajectory_data = []
        self.error_data = []
        self.frame_count = 0
    def add_pose(self, timestamp, pose, gt_pose=None):
        self.frame_count += 1
        pose_data = {'frame': self.frame_count, 'timestamp': float(timestamp), 'pose': pose.tolist() if isinstance(pose, np.ndarray) else pose}
        if gt_pose is not None:
            pose_data['gt_pose'] = gt_pose.tolist() if isinstance(gt_pose, np.ndarray) else gt_pose
            error = self._compute_error(pose, gt_pose)
            pose_data['error'] = float(error)
            self.error_data.append({'frame': self.frame_count, 'error': float(error)})
        self.trajectory_data.append(pose_data)
        return pose_data
    def _compute_error(self, pose, gt_pose):
        if isinstance(pose, np.ndarray) and len(pose.shape) == 2:
            pos = pose[:3, 3]
            gt_pos = gt_pose[:3, 3]
        else:
            pos = np.array(pose)[:3]
            gt_pos = np.array(gt_pose)[:3]
        return float(np.linalg.norm(pos - gt_pos))
    def get_live_data(self):
        return {'trajectory': self.trajectory_data[-100:], 'errors': self.error_data[-100:], 'frame_count': self.frame_count}
    def get_full_data(self):
        return {'trajectory': self.trajectory_data, 'errors': self.error_data, 'frame_count': self.frame_count}
    def save(self):
        with open(self.output_dir / 'visualization.json', 'w') as f:
            json.dump(self.get_full_data(), f)
