from pathlib import Path
import numpy as np
import cv2
import json
import config

class DataLoader:
    def __init__(self, dataset_path):
        self.path = Path(dataset_path)
        self.metadata = self._load_metadata()
        self.frame_cache = {}
    def _load_metadata(self):
        meta_file = self.path / 'metadata.json'
        if meta_file.exists():
            with open(meta_file) as f:
                return json.load(f)
        return {}
    def load_image(self, frame_id, sensor='image_0'):
        cache_key = f'{frame_id}_{sensor}'
        if cache_key in self.frame_cache:
            return self.frame_cache[cache_key]
        frames = self.metadata.get('frames', [])
        if frame_id >= len(frames):
            return None
        frame = frames[frame_id]
        images = frame.get('images', {})
        if sensor not in images:
            return None
        img_path = Path(images[sensor])
        if not img_path.exists():
            return None
        img = cv2.imread(str(img_path))
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.frame_cache[cache_key] = img
        return img
    def load_depth(self, frame_id):
        frames = self.metadata.get('frames', [])
        if frame_id >= len(frames):
            return None
        frame = frames[frame_id]
        images = frame.get('images', {})
        if 'depth' not in images:
            return None
        depth_path = Path(images['depth'])
        if not depth_path.exists():
            return None
        depth = cv2.imread(str(depth_path), cv2.IMREAD_ANYDEPTH)
        return depth
    def load_lidar(self, frame_id):
        return None
    def get_frame_data(self, frame_id):
        frames = self.metadata.get('frames', [])
        if frame_id >= len(frames):
            return None
        frame = frames[frame_id]
        data = {'frame_id': frame_id, 'timestamp': frame.get('timestamp', frame_id / 10.0), 'images': {}}
        for sensor in frame.get('images', {}).keys():
            img = self.load_image(frame_id, sensor)
            if img is not None:
                data['images'][sensor] = img
        depth = self.load_depth(frame_id)
        if depth is not None:
            data['depth'] = depth
        lidar = self.load_lidar(frame_id)
        if lidar is not None:
            data['lidar'] = lidar
        return data
    def get_num_frames(self):
        return len(self.metadata.get('frames', []))
    def get_ground_truth(self):
        gt = self.metadata.get('ground_truth')
        if gt is None:
            return None
        if isinstance(gt, list) and len(gt) > 0:
            if isinstance(gt[0], dict):
                poses = []
                for item in gt:
                    if 'pose' in item:
                        poses.append(item['pose'])
                    elif 'position' in item and 'quaternion' in item:
                        pose = self._quat_to_matrix(item['position'], item['quaternion'])
                        poses.append(pose)
                return np.array(poses)
            else:
                return np.array(gt)
        return None
    def _quat_to_matrix(self, pos, quat):
        from scipy.spatial.transform import Rotation
        rot = Rotation.from_quat(quat)
        mat = np.eye(4)
        mat[:3, :3] = rot.as_matrix()
        mat[:3, 3] = pos
        return mat
    def get_calibration(self):
        return self.metadata.get('calibration', {})
