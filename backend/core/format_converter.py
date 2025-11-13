from pathlib import Path
import numpy as np
import json
import config
from backend.core.format_detector import detect_format

class DatasetConverter:
    def __init__(self, source_path, output_path):
        self.source = Path(source_path)
        self.output = Path(output_path)
        self.format = detect_format(source_path)
        self.output.mkdir(parents=True, exist_ok=True)

    def convert(self):
        if self.format == 'kitti':
            return self._convert_kitti()
        elif self.format == 'euroc':
            return self._convert_euroc()
        elif self.format == 'tum':
            return self._convert_tum()
        elif self.format == 'rosbag':
            return self._convert_rosbag()
        else:
            return self._convert_custom()

    def _convert_kitti(self):
        data = {'format': 'kitti', 'sensors': [], 'frames': []}

        calib_file = self.source / 'calib.txt'
        if calib_file.exists():
            calib = self._parse_kitti_calib(calib_file)
            data['calibration'] = calib

        seq_dir = self.source / 'sequences'
        if seq_dir.exists():
            for seq in seq_dir.iterdir():
                if seq.is_dir():
                    self._process_kitti_sequence(seq, data)

        poses_dir = self.source / 'poses'
        if poses_dir.exists():
            for pose_file in poses_dir.glob('*.txt'):
                data['ground_truth'] = self._load_kitti_poses(pose_file)

        self._save_metadata(data)
        return data

    def _convert_euroc(self):
        data = {'format': 'euroc', 'sensors': [], 'frames': []}

        mav0 = self.source / 'mav0'
        if not mav0.exists():
            return data

        for cam in ['cam0', 'cam1']:
            cam_dir = mav0 / cam
            if cam_dir.exists():
                data['sensors'].append(f'camera_{cam}')
                self._process_euroc_camera(cam_dir, data, cam)

        imu_dir = mav0 / 'imu0'
        if imu_dir.exists():
            data['sensors'].append('imu')
            self._process_euroc_imu(imu_dir, data)

        gt_file = mav0 / 'state_groundtruth_estimate0' / 'data.csv'
        if gt_file.exists():
            data['ground_truth'] = self._load_euroc_gt(gt_file)

        self._save_metadata(data)
        return data

    def _convert_tum(self):
        data = {'format': 'tum', 'sensors': [], 'frames': []}

        rgb_file = self.source / 'rgb.txt'
        depth_file = self.source / 'depth.txt'

        if rgb_file.exists():
            data['sensors'].append('rgb')
            self._process_tum_images(rgb_file, data, 'rgb')

        if depth_file.exists():
            data['sensors'].append('depth')
            self._process_tum_images(depth_file, data, 'depth')

        gt_file = self.source / 'groundtruth.txt'
        if gt_file.exists():
            data['ground_truth'] = self._load_tum_gt(gt_file)

        self._save_metadata(data)
        return data

    def _convert_rosbag(self):
        data = {'format': 'rosbag', 'sensors': [], 'frames': [], 'topics': []}

        bag_files = list(self.source.glob('*.bag'))
        if bag_files:
            data['bag_file'] = str(bag_files[0])

        self._save_metadata(data)
        return data

    def _convert_custom(self):
        data = {'format': 'custom', 'sensors': [], 'frames': []}
        self._save_metadata(data)
        return data

    def _parse_kitti_calib(self, calib_file):
        calib = {}
        with open(calib_file) as f:
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    calib[key.strip()] = [float(x) for x in value.strip().split()]
        return calib

    def _process_kitti_sequence(self, seq_dir, data):
        image_dirs = [seq_dir / 'image_0', seq_dir / 'image_1', seq_dir / 'image_2', seq_dir / 'image_3']

        for img_dir in image_dirs:
            if img_dir.exists():
                images = sorted(img_dir.glob('*.png'))
                for idx, img in enumerate(images):
                    frame = {'id': idx, 'timestamp': idx / 10.0, 'images': {img_dir.name: str(img)}}
                    if idx < len(data['frames']):
                        data['frames'][idx]['images'][img_dir.name] = str(img)
                    else:
                        data['frames'].append(frame)

        velodyne_dir = seq_dir / 'velodyne'
        if velodyne_dir.exists():
            data['sensors'].append('lidar')

    def _process_euroc_camera(self, cam_dir, data, cam_name):
        data_csv = cam_dir / 'data.csv'
        if not data_csv.exists():
            return

        with open(data_csv) as f:
            lines = f.readlines()[1:]
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    timestamp = float(parts[0]) / 1e9
                    image_path = cam_dir / 'data' / parts[1]
                    frame = {'timestamp': timestamp, 'images': {cam_name: str(image_path)}}
                    data['frames'].append(frame)

    def _process_euroc_imu(self, imu_dir, data):
        data_csv = imu_dir / 'data.csv'
        if not data_csv.exists():
            return

        imu_data = []
        with open(data_csv) as f:
            lines = f.readlines()[1:]
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 7:
                    timestamp = float(parts[0]) / 1e9
                    gyro = [float(parts[1]), float(parts[2]), float(parts[3])]
                    accel = [float(parts[4]), float(parts[5]), float(parts[6])]
                    imu_data.append({'timestamp': timestamp, 'gyro': gyro, 'accel': accel})
        data['imu'] = imu_data

    def _process_tum_images(self, txt_file, data, sensor_type):
        with open(txt_file) as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('#'):
                    continue
                parts = line.strip().split()
                if len(parts) >= 2:
                    timestamp = float(parts[0])
                    image_path = self.source / parts[1]
                    frame = {'timestamp': timestamp, 'images': {sensor_type: str(image_path)}}
                    data['frames'].append(frame)

    def _load_kitti_poses(self, pose_file):
        poses = []
        with open(pose_file) as f:
            for line in f:
                values = [float(x) for x in line.strip().split()]
                if len(values) == 12:
                    mat = np.array(values).reshape(3, 4)
                    pose = np.eye(4)
                    pose[:3, :] = mat
                    poses.append(pose.tolist())
        return poses

    def _load_euroc_gt(self, gt_file):
        poses = []
        with open(gt_file) as f:
            lines = f.readlines()[1:]
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 8:
                    timestamp = float(parts[0]) / 1e9
                    pos = [float(parts[1]), float(parts[2]), float(parts[3])]
                    quat = [float(parts[4]), float(parts[5]), float(parts[6]), float(parts[7])]
                    poses.append({'timestamp': timestamp, 'position': pos, 'quaternion': quat})
        return poses

    def _load_tum_gt(self, gt_file):
        poses = []
        with open(gt_file) as f:
            for line in f:
                if line.startswith('#'):
                    continue
                parts = line.strip().split()
                if len(parts) >= 8:
                    timestamp = float(parts[0])
                    pos = [float(parts[1]), float(parts[2]), float(parts[3])]
                    quat = [float(parts[4]), float(parts[5]), float(parts[6]), float(parts[7])]
                    poses.append({'timestamp': timestamp, 'position': pos, 'quaternion': quat})
        return poses

    def _save_metadata(self, data):
        metadata_file = self.output / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
