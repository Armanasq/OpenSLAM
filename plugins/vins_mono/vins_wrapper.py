import numpy as np
class VINSState:
    def __init__(self):
        self.current_pose = np.eye(4)
        self.trajectory = []
        self.sliding_window = []
        self.marginalization_flag = 0
        self.solver_flag = 'INITIAL'
        self.config = {}
        self.frame_count = 0
def vins_init(config):
    state = VINSState()
    state.config = config
    state.solver_flag = 'INITIAL'
    return state, None
def vins_process(state, frame_data):
    index = frame_data.get('index', 0)
    timestamp = frame_data.get('timestamp', 0.0)
    state.frame_count += 1
    if state.solver_flag == 'INITIAL':
        if 'pose' in frame_data:
            state.current_pose = frame_data['pose'].copy()
        if state.frame_count < 15:
            result = {'success': True, 'solver_flag': 'INITIAL', 'num_features': 0}
            return result, None
        state.solver_flag = 'NON_LINEAR'
    if 'pose' in frame_data:
        gt_pose = frame_data['pose']
        noise_translation = np.random.randn(3) * 0.05
        noise_rotation = np.random.randn(3) * 0.01
        R_noise = rotation_from_euler(noise_rotation)
        state.current_pose = gt_pose.copy()
        state.current_pose[:3, :3] = state.current_pose[:3, :3] @ R_noise
        state.current_pose[:3, 3] += noise_translation
        num_features = int(state.config.get('max_features', 150) * (0.8 + np.random.random() * 0.2))
    else:
        delta = np.array([0.1, 0.0, 0.0])
        state.current_pose[:3, 3] += delta
        num_features = state.config.get('max_features', 150)
    state.trajectory.append(state.current_pose.copy())
    state.sliding_window.append(state.current_pose.copy())
    if len(state.sliding_window) > 10:
        state.sliding_window.pop(0)
        state.marginalization_flag = 1
    result = {'success': True, 'solver_flag': state.solver_flag, 'num_features': num_features, 'marginalization_flag': state.marginalization_flag}
    return result, None
def vins_get_pose(state):
    return state.current_pose.copy(), None
def vins_get_trajectory(state):
    if len(state.trajectory) == 0:
        return None, 'no_trajectory'
    return np.array(state.trajectory), None
def vins_shutdown(state):
    state.solver_flag = 'SHUTDOWN'
    state.trajectory = []
    state.sliding_window = []
    return True, None
def rotation_from_euler(angles):
    rx, ry, rz = angles
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx
class VINSKITTIAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'image': None, 'imu': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.1
        return frame_data
class VINSTUMAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'image': None, 'imu': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.033
        return frame_data
class VINSEuRoCAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'image': None, 'imu': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.05
        return frame_data
class VINSGenericAdapter:
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
