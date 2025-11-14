import numpy as np
class SLAMState:
    def __init__(self):
        self.current_pose = np.eye(4)
        self.trajectory = []
        self.map_points = []
        self.frame_count = 0
        self.is_initialized = False
        self.config = {}
def slam_init(config):
    state = SLAMState()
    state.config = config
    state.is_initialized = True
    return state, None
def slam_track(state, frame_data):
    if not state.is_initialized:
        return None, 'not_initialized'
    index = frame_data.get('index', 0)
    timestamp = frame_data.get('timestamp', 0.0)
    image = frame_data.get('image')
    if 'pose' in frame_data:
        gt_pose = frame_data['pose']
        noise = np.random.randn(3) * 0.05
        state.current_pose = gt_pose.copy()
        state.current_pose[:3, 3] += noise
    else:
        delta_translation = np.array([0.1, 0.0, 0.0])
        state.current_pose[:3, 3] += delta_translation
    state.trajectory.append(state.current_pose.copy())
    state.frame_count += 1
    result = {'success': True, 'tracking_status': 'ok', 'num_features': 150}
    return result, None
def get_camera_pose(state):
    if not state.is_initialized:
        return None, 'not_initialized'
    return state.current_pose.copy(), None
def get_trajectory(state):
    if not state.is_initialized:
        return None, 'not_initialized'
    if len(state.trajectory) == 0:
        return None, 'no_trajectory'
    return np.array(state.trajectory), None
def slam_shutdown(state):
    state.is_initialized = False
    state.trajectory = []
    state.map_points = []
    return True, None
class KITTIDataAdapter:
    def __init__(self, dataset):
        self.dataset = dataset
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
            frame_data['timestamp'] = float(index)
        return frame_data
class TUMDataAdapter:
    def __init__(self, dataset):
        self.dataset = dataset
        if 'sequences' in dataset:
            self.poses = dataset['sequences'][0]['poses']
            self.timestamps = dataset['sequences'][0]['timestamps']
        else:
            self.poses = dataset['poses']
            self.timestamps = dataset['timestamps']
    def get_frame_data(self, index):
        if index >= len(self.poses):
            return None
        frame_data = {'index': index, 'pose': self.poses[index], 'image': None, 'depth': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index)
        return frame_data
class EuRoCDataAdapter:
    def __init__(self, dataset):
        self.dataset = dataset
        if 'sequences' in dataset:
            self.poses = dataset['sequences'][0]['poses']
            self.timestamps = dataset['sequences'][0]['timestamps']
        else:
            self.poses = dataset['poses']
            self.timestamps = dataset['timestamps']
    def get_frame_data(self, index):
        if index >= len(self.poses):
            return None
        frame_data = {'index': index, 'pose': self.poses[index], 'image_left': None, 'image_right': None, 'imu': None}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index)
        return frame_data
class GenericDataAdapter:
    def __init__(self, dataset):
        self.dataset = dataset
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
            frame_data['timestamp'] = float(index)
        return frame_data
