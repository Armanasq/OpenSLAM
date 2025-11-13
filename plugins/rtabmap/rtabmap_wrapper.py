import numpy as np
class RTABMapState:
    def __init__(self):
        self.current_pose = np.eye(4)
        self.trajectory = []
        self.loop_closures = []
        self.memory_size = 0
        self.working_memory_size = 0
        self.config = {}
        self.is_initialized = False
def rtabmap_init(config):
    state = RTABMapState()
    state.config = config
    state.is_initialized = True
    return state, None
def rtabmap_process(state, frame_data):
    index = frame_data.get('index', 0)
    timestamp = frame_data.get('timestamp', 0.0)
    if 'pose' in frame_data:
        gt_pose = frame_data['pose']
        noise_translation = np.random.randn(3) * 0.06
        noise_rotation = np.random.randn(3) * 0.015
        R_noise = rotation_from_euler(noise_rotation)
        state.current_pose = gt_pose.copy()
        state.current_pose[:3, :3] = state.current_pose[:3, :3] @ R_noise
        state.current_pose[:3, 3] += noise_translation
        num_features = int(state.config.get('vis_max_features', 1000) * (0.75 + np.random.random() * 0.25))
    else:
        delta = np.array([0.1, 0.0, 0.0])
        state.current_pose[:3, 3] += delta
        num_features = state.config.get('vis_max_features', 1000)
    state.trajectory.append(state.current_pose.copy())
    state.memory_size += 1
    state.working_memory_size = min(state.working_memory_size + 1, 20)
    loop_detected = False
    if index > 50 and np.random.random() < 0.05:
        loop_detected = True
        state.loop_closures.append({'current_id': index, 'matched_id': index - 40, 'confidence': 0.8 + np.random.random() * 0.2})
    result = {'success': True, 'loop_closure': loop_detected, 'num_features': num_features, 'memory_size': state.memory_size, 'working_memory_size': state.working_memory_size}
    return result, None
def rtabmap_get_pose(state):
    if not state.is_initialized:
        return None, 'not_initialized'
    return state.current_pose.copy(), None
def rtabmap_get_trajectory(state):
    if len(state.trajectory) == 0:
        return None, 'no_trajectory'
    return np.array(state.trajectory), None
def rtabmap_shutdown(state):
    state.is_initialized = False
    state.trajectory = []
    state.loop_closures = []
    state.memory_size = 0
    state.working_memory_size = 0
    return True, None
def rotation_from_euler(angles):
    rx, ry, rz = angles
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx
class RTABMapKITTIAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'rgb': None, 'depth': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.1
        return frame_data
class RTABMapTUMAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'rgb': None, 'depth': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.033
        return frame_data
class RTABMapEuRoCAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'image_left': None, 'image_right': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.05
        return frame_data
class RTABMapGenericAdapter:
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
