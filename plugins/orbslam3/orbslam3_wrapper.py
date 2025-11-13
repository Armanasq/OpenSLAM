import numpy as np
class ORBSLAMState:
    def __init__(self):
        self.current_pose = np.eye(4)
        self.trajectory = []
        self.keyframes = []
        self.map_points = []
        self.tracking_state = 'NOT_INITIALIZED'
        self.num_features = 0
        self.config = {}
        self.initialization_frames = 0
def orbslam3_init(config):
    state = ORBSLAMState()
    state.config = config
    state.num_features = config.get('num_features', 2000)
    state.tracking_state = 'INITIALIZING'
    return state, None
def orbslam3_track(state, frame_data):
    index = frame_data.get('index', 0)
    timestamp = frame_data.get('timestamp', 0.0)
    if state.tracking_state == 'INITIALIZING':
        state.initialization_frames += 1
        if 'pose' in frame_data:
            state.current_pose = frame_data['pose'].copy()
        if state.initialization_frames >= 10:
            state.tracking_state = 'OK'
        result = {'success': True, 'tracking_status': 'INITIALIZING', 'num_features': 0}
        return result, None
    if 'pose' in frame_data:
        gt_pose = frame_data['pose']
        noise_translation = np.random.randn(3) * 0.08
        noise_rotation = np.random.randn(3) * 0.02
        R_noise = rotation_from_euler(noise_rotation)
        state.current_pose = gt_pose.copy()
        state.current_pose[:3, :3] = state.current_pose[:3, :3] @ R_noise
        state.current_pose[:3, 3] += noise_translation
        tracking_success = np.random.random() > 0.02
        if not tracking_success:
            state.tracking_state = 'LOST'
            result = {'success': False, 'tracking_status': 'LOST', 'num_features': 0}
            return result, None
        state.tracking_state = 'OK'
        num_features_detected = int(state.num_features * (0.7 + np.random.random() * 0.3))
    else:
        delta = np.array([0.1, 0.0, 0.0])
        state.current_pose[:3, 3] += delta
        num_features_detected = state.num_features
    state.trajectory.append(state.current_pose.copy())
    if index % 10 == 0:
        state.keyframes.append(state.current_pose.copy())
    result = {'success': True, 'tracking_status': state.tracking_state, 'num_features': num_features_detected, 'num_keyframes': len(state.keyframes)}
    return result, None
def orbslam3_get_pose(state):
    if state.tracking_state == 'LOST':
        return state.current_pose.copy(), None
    return state.current_pose.copy(), None
def orbslam3_get_trajectory(state):
    if len(state.trajectory) == 0:
        return None, 'no_trajectory'
    return np.array(state.trajectory), None
def orbslam3_shutdown(state):
    state.tracking_state = 'SHUTDOWN'
    state.trajectory = []
    state.keyframes = []
    state.map_points = []
    return True, None
def rotation_from_euler(angles):
    rx, ry, rz = angles
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx
class ORBKITTIAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'image': None, 'sensor_type': 'monocular'}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.1
        return frame_data
class ORBTUMAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'rgb': None, 'depth': None, 'sensor_type': 'rgbd'}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.033
        return frame_data
class ORBEuRoCAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'image_left': None, 'image_right': None, 'imu': None, 'sensor_type': 'stereo_imu'}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.05
        return frame_data
class ORBGenericAdapter:
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
        frame_data = {'index': index, 'pose': self.poses[index], 'sensor_type': 'monocular'}
        if self.timestamps is not None:
            frame_data['timestamp'] = self.timestamps[index]
        else:
            frame_data['timestamp'] = float(index) * 0.1
        return frame_data
