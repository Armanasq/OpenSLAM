import numpy as np
from pathlib import Path
import csv
from config import openslam_config as cfg
def detect_format(path):
    path = Path(path)
    if not path.exists():
        return None, 'path_not_exist'
    if path.is_file():
        if path.suffix == '.bag':
            return 'rosbag', None
        if path.name == 'groundtruth.txt' or path.name == 'rgb.txt':
            return 'tum', None
        if 'timestamps' in path.name or path.parent.name in ['cam0', 'cam1', 'imu0']:
            return 'euroc', None
        return 'custom', None
    sequences_dir = path / 'sequences'
    if sequences_dir.exists():
        return 'kitti', None
    mav_dir = path / 'mav0'
    if mav_dir.exists():
        return 'euroc', None
    rgb_file = path / 'rgb.txt'
    depth_file = path / 'depth.txt'
    if rgb_file.exists() and depth_file.exists():
        return 'tum', None
    return 'custom', None
def validate_path(path):
    path = Path(path)
    if not path.exists():
        return False, 'path_not_exist'
    if not (path.is_dir() or path.is_file()):
        return False, 'invalid_path_type'
    return True, None
def load_kitti_poses(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        return None, 'file_not_exist'
    poses = []
    with open(file_path, 'r') as f:
        for line in f:
            values = line.strip().split()
            if len(values) != 12:
                return None, 'invalid_pose_format'
            matrix = np.array([float(v) for v in values]).reshape(3, 4)
            pose = np.eye(4)
            pose[:3, :] = matrix
            poses.append(pose)
    if len(poses) == 0:
        return None, 'empty_file'
    return np.array(poses), None
def load_tum_poses(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        return None, 'file_not_exist'
    timestamps = []
    poses = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            values = line.strip().split()
            if len(values) != 8:
                return None, 'invalid_pose_format'
            timestamp = float(values[0])
            x, y, z = float(values[1]), float(values[2]), float(values[3])
            qx, qy, qz, qw = float(values[4]), float(values[5]), float(values[6]), float(values[7])
            pose = quaternion_to_matrix(qw, qx, qy, qz, x, y, z)
            timestamps.append(timestamp)
            poses.append(pose)
    if len(poses) == 0:
        return None, 'empty_file'
    return {'timestamps': np.array(timestamps), 'poses': np.array(poses)}, None
def load_euroc_poses(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        return None, 'file_not_exist'
    timestamps = []
    poses = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            return None, 'empty_file'
        for row in reader:
            if len(row) != 8:
                return None, 'invalid_pose_format'
            timestamp = int(row[0]) / 1e9
            x, y, z = float(row[1]), float(row[2]), float(row[3])
            qw, qx, qy, qz = float(row[4]), float(row[5]), float(row[6]), float(row[7])
            pose = quaternion_to_matrix(qw, qx, qy, qz, x, y, z)
            timestamps.append(timestamp)
            poses.append(pose)
    if len(poses) == 0:
        return None, 'empty_file'
    return {'timestamps': np.array(timestamps), 'poses': np.array(poses)}, None
def quaternion_to_matrix(qw, qx, qy, qz, x, y, z):
    norm = np.sqrt(qw**2 + qx**2 + qy**2 + qz**2)
    qw, qx, qy, qz = qw/norm, qx/norm, qy/norm, qz/norm
    R = np.array([
        [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
        [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
        [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]
    ])
    pose = np.eye(4)
    pose[:3, :3] = R
    pose[:3, 3] = [x, y, z]
    return pose
def load_rosbag_poses(file_path, pose_topic='/slam/pose'):
    file_path = Path(file_path)
    if not file_path.exists():
        return None, 'file_not_exist'
    rosbag_available = False
    rospy_available = False
    try:
        import rosbag
        rosbag_available = True
    except ImportError:
        pass
    try:
        from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
        from nav_msgs.msg import Odometry
        rospy_available = True
    except ImportError:
        pass
    if not rosbag_available or not rospy_available:
        return None, 'rosbag_not_available'
    timestamps = []
    poses = []
    bag = rosbag.Bag(str(file_path))
    for topic, msg, t in bag.read_messages(topics=[pose_topic]):
        timestamp = t.to_sec()
        if hasattr(msg, 'pose'):
            if hasattr(msg.pose, 'pose'):
                pose_msg = msg.pose.pose
            else:
                pose_msg = msg.pose
        else:
            continue
        x = pose_msg.position.x
        y = pose_msg.position.y
        z = pose_msg.position.z
        qx = pose_msg.orientation.x
        qy = pose_msg.orientation.y
        qz = pose_msg.orientation.z
        qw = pose_msg.orientation.w
        pose = quaternion_to_matrix(qw, qx, qy, qz, x, y, z)
        timestamps.append(timestamp)
        poses.append(pose)
    bag.close()
    if len(poses) == 0:
        return None, 'no_poses_found'
    return {'timestamps': np.array(timestamps), 'poses': np.array(poses)}, None
def load_custom_format(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        return None, 'file_not_exist'
    with open(file_path, 'r') as f:
        first_line = f.readline().strip()
        if not first_line or first_line.startswith('#'):
            f.seek(0)
            for line in f:
                if not line.startswith('#') and line.strip():
                    first_line = line.strip()
                    break
        values = first_line.replace(',', ' ').split()
        num_values = len(values)
    if num_values < 3:
        return None, 'invalid_format'
    timestamps = []
    poses = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            values = line.strip().replace(',', ' ').split()
            if len(values) < 3:
                continue
            if num_values == 3:
                x, y, z = float(values[0]), float(values[1]), float(values[2])
                pose = np.eye(4)
                pose[:3, 3] = [x, y, z]
                poses.append(pose)
            elif num_values == 4:
                timestamp = float(values[0])
                x, y, z = float(values[1]), float(values[2]), float(values[3])
                pose = np.eye(4)
                pose[:3, 3] = [x, y, z]
                timestamps.append(timestamp)
                poses.append(pose)
            elif num_values == 7:
                x, y, z = float(values[0]), float(values[1]), float(values[2])
                qx, qy, qz, qw = float(values[3]), float(values[4]), float(values[5]), float(values[6])
                pose = quaternion_to_matrix(qw, qx, qy, qz, x, y, z)
                poses.append(pose)
            elif num_values == 8:
                timestamp = float(values[0])
                x, y, z = float(values[1]), float(values[2]), float(values[3])
                qx, qy, qz, qw = float(values[4]), float(values[5]), float(values[6]), float(values[7])
                pose = quaternion_to_matrix(qw, qx, qy, qz, x, y, z)
                timestamps.append(timestamp)
                poses.append(pose)
            elif num_values == 12:
                matrix = np.array([float(v) for v in values]).reshape(3, 4)
                pose = np.eye(4)
                pose[:3, :] = matrix
                poses.append(pose)
            elif num_values == 13:
                timestamp = float(values[0])
                matrix = np.array([float(v) for v in values[1:]]).reshape(3, 4)
                pose = np.eye(4)
                pose[:3, :] = matrix
                timestamps.append(timestamp)
                poses.append(pose)
            else:
                continue
    if len(poses) == 0:
        return None, 'no_poses_parsed'
    if len(timestamps) == 0:
        return {'timestamps': None, 'poses': np.array(poses)}, None
    return {'timestamps': np.array(timestamps), 'poses': np.array(poses)}, None
def load_dataset(path, format_type=None):
    valid, error = validate_path(path)
    if not valid:
        return None, error
    if format_type is None:
        format_type, error = detect_format(path)
        if format_type is None:
            return None, error
    path = Path(path)
    if format_type == 'kitti':
        return load_kitti_dataset(path)
    elif format_type == 'tum':
        return load_tum_dataset(path)
    elif format_type == 'euroc':
        return load_euroc_dataset(path)
    elif format_type == 'rosbag':
        result, error = load_rosbag_poses(path)
        if error:
            return None, error
        return {'name': path.stem, 'format': 'rosbag', 'poses': result['poses'], 'timestamps': result['timestamps'], 'path': str(path)}, None
    elif format_type == 'custom':
        result, error = load_custom_format(path)
        if error:
            return None, error
        return {'name': path.stem, 'format': 'custom', 'poses': result['poses'], 'timestamps': result['timestamps'], 'path': str(path)}, None
    else:
        return None, 'unsupported_format'
def load_kitti_dataset(path):
    path = Path(path)
    if path.is_file():
        poses, error = load_kitti_poses(path)
        if error:
            return None, error
        return {'name': path.stem, 'format': 'kitti', 'poses': poses, 'timestamps': None, 'path': str(path)}, None
    sequences_dir = path / 'sequences'
    if not sequences_dir.exists():
        sequences_dir = path
    sequences = []
    for seq_dir in sorted(sequences_dir.iterdir()):
        if not seq_dir.is_dir():
            continue
        pose_file = seq_dir / 'poses.txt'
        if not pose_file.exists():
            continue
        poses, error = load_kitti_poses(pose_file)
        if error:
            continue
        sequences.append({'name': seq_dir.name, 'poses': poses, 'timestamps': None})
    if len(sequences) == 0:
        return None, 'no_sequences_found'
    return {'name': path.name, 'format': 'kitti', 'sequences': sequences, 'path': str(path)}, None
def load_tum_dataset(path):
    path = Path(path)
    if path.is_file():
        result, error = load_tum_poses(path)
        if error:
            return None, error
        return {'name': path.stem, 'format': 'tum', 'poses': result['poses'], 'timestamps': result['timestamps'], 'path': str(path)}, None
    gt_file = path / 'groundtruth.txt'
    if not gt_file.exists():
        return None, 'groundtruth_file_not_found'
    result, error = load_tum_poses(gt_file)
    if error:
        return None, error
    return {'name': path.name, 'format': 'tum', 'poses': result['poses'], 'timestamps': result['timestamps'], 'path': str(path)}, None
def load_euroc_dataset(path):
    path = Path(path)
    if path.is_file():
        result, error = load_euroc_poses(path)
        if error:
            return None, error
        return {'name': path.stem, 'format': 'euroc', 'poses': result['poses'], 'timestamps': result['timestamps'], 'path': str(path)}, None
    mav_dir = path / 'mav0'
    if not mav_dir.exists():
        mav_dir = path
    gt_file = mav_dir / 'state_groundtruth_estimate0' / 'data.csv'
    if not gt_file.exists():
        return None, 'groundtruth_file_not_found'
    result, error = load_euroc_poses(gt_file)
    if error:
        return None, error
    return {'name': path.name, 'format': 'euroc', 'poses': result['poses'], 'timestamps': result['timestamps'], 'path': str(path)}, None
def get_dataset_info(dataset):
    info = {'name': dataset['name'], 'format': dataset['format'], 'path': dataset['path']}
    if 'sequences' in dataset:
        info['sequences'] = len(dataset['sequences'])
        info['total_frames'] = sum(len(seq['poses']) for seq in dataset['sequences'])
    else:
        info['frames'] = len(dataset['poses'])
        info['sequences'] = 1
    if dataset.get('timestamps') is not None:
        timestamps = dataset['timestamps']
        info['duration'] = float(timestamps[-1] - timestamps[0])
        info['frequency'] = len(timestamps) / info['duration'] if info['duration'] > 0 else 0
    return info
