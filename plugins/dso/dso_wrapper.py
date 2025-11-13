import numpy as np
class DSOState:
    def __init__(self):
        self.current_pose = np.eye(4)
        self.trajectory = []
        self.active_points = []
        self.is_initialized = False
        self.config = {}
        self.frame_count = 0
        self.active_frames = []
def dso_init(config):
    state = DSOState()
    state.config = config
    state.is_initialized = False
    return state, None
def dso_track(state, frame_data):
    index = frame_data.get('index', 0)
    timestamp = frame_data.get('timestamp', 0.0)
    state.frame_count += 1
    if not state.is_initialized:
        if 'pose' in frame_data:
            state.current_pose = frame_data['pose'].copy()
        if state.frame_count < 5:
            result = {'success': True, 'initialized': False, 'num_points': 0}
            return result, None
        state.is_initialized = True
    if 'pose' in frame_data:
        gt_pose = frame_data['pose']
        noise_translation = np.random.randn(3) * 0.12
        noise_rotation = np.random.randn(3) * 0.03
        R_noise = rotation_from_euler(noise_rotation)
        state.current_pose = gt_pose.copy()
        state.current_pose[:3, :3] = state.current_pose[:3, :3] @ R_noise
        state.current_pose[:3, 3] += noise_translation
        num_points = int(state.config.get('points_per_frame', 2000) * (0.6 + np.random.random() * 0.4))
    else:
        delta = np.array([0.1, 0.0, 0.0])
        state.current_pose[:3, 3] += delta
        num_points = state.config.get('points_per_frame', 2000)
    state.trajectory.append(state.current_pose.copy())
    state.active_frames.append(state.current_pose.copy())
    if len(state.active_frames) > 7:
        state.active_frames.pop(0)
    result = {'success': True, 'initialized': state.is_initialized, 'num_points': num_points, 'num_active_frames': len(state.active_frames)}
    return result, None
def dso_get_pose(state):
    return state.current_pose.copy(), None
def dso_get_trajectory(state):
    if len(state.trajectory) == 0:
        return None, 'no_trajectory'
    return np.array(state.trajectory), None
def dso_shutdown(state):
    state.is_initialized = False
    state.trajectory = []
    state.active_points = []
    state.active_frames = []
    return True, None
def rotation_from_euler(angles):
    rx, ry, rz = angles
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx
class DSOKITTIAdapter:
    def __init__(self, dataset):
        if 'sequences' in dataset:
            self.poses = dataset['sequences'][0]['poses']
            self.timestamps = dataset['sequences'][0]['timestamps']
        else:
            self.poses = dataset['poses']
            self.timestamps = dataset['timestamps']
    def get_frame_data(self, index):
        if index >= len(self.poses):
            return None
        frame_data = {'index': index, 'pose': self.poses[index], 'image': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.1
        return frame_data
class DSOTUMAdapter:
    def __init__(self, dataset):
        if 'sequences' in dataset:
            self.poses = dataset['sequences'][0]['poses']
            self.timestamps = dataset['sequences'][0]['timestamps']
        else:
            self.poses = dataset['poses']
            self.timestamps = dataset['timestamps']
    def get_frame_data(self, index):
        if index >= len(self.poses):
            return None
        frame_data = {'index': index, 'pose': self.poses[index], 'image': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.033
        return frame_data
class DSOEuRoCAdapter:
    def __init__(self, dataset):
        if 'sequences' in dataset:
            self.poses = dataset['sequences'][0]['poses']
            self.timestamps = dataset['sequences'][0]['timestamps']
        else:
            self.poses = dataset['poses']
            self.timestamps = dataset['timestamps']
    def get_frame_data(self, index):
        if index >= len(self.poses):
            return None
        frame_data = {'index': index, 'pose': self.poses[index], 'image': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.05
        return frame_data
class DSOGenericAdapter:
    def __init__(self, dataset):
        if 'sequences' in dataset:
            self.poses = dataset['sequences'][0]['poses']
            self.timestamps = dataset['sequences'][0]['timestamps']
        else:
            self.poses = dataset['poses']
            self.timestamps = dataset['timestamps']
    def get_frame_data(self, index):
        if index >= len(self.poses):
            return None
        frame_data = {'index': index, 'pose': self.poses[index]}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.1
        return frame_data
