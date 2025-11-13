import numpy as np
from pathlib import Path
import json
import config

class SLAMAlgorithm:
    def initialize(self, cfg):
        raise NotImplementedError

    def process_frame(self, frame_data):
        raise NotImplementedError

    def finalize(self):
        raise NotImplementedError

class FrameData:
    def __init__(self, data):
        self.timestamp = data.get('timestamp', 0.0)
        self.frame_id = data.get('frame_id', 0)
        self.image = data.get('image')
        self.images = data.get('images', {})
        self.depth = data.get('depth')
        self.imu_data = data.get('imu_data', [])
        self.lidar_points = data.get('lidar_points')
        self.metadata = data.get('metadata', {})

class PoseEstimate:
    def __init__(self, timestamp, pose, covariance=None, confidence=1.0):
        self.timestamp = timestamp
        self.pose = np.array(pose)
        self.covariance = covariance
        self.confidence = confidence

    def to_dict(self):
        return {'timestamp': float(self.timestamp), 'pose': self.pose.tolist(), 'covariance': self.covariance.tolist() if self.covariance is not None else None, 'confidence': float(self.confidence)}

class Results:
    def __init__(self, trajectory, map_points=None, timing=None, metadata=None):
        self.trajectory = np.array(trajectory)
        self.map_points = np.array(map_points) if map_points is not None else None
        self.timing = timing if timing is not None else {}
        self.metadata = metadata if metadata is not None else {}

    def to_dict(self):
        return {'trajectory': self.trajectory.tolist(), 'map_points': self.map_points.tolist() if self.map_points is not None else None, 'timing': self.timing, 'metadata': self.metadata}

class AlgorithmRunner:
    def __init__(self, algorithm, dataset, output_dir):
        self.algorithm = algorithm
        self.dataset = dataset
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.poses = []
        self.timestamps = []

    def run(self, on_frame=None):
        cfg = {'dataset_path': str(self.dataset.path), 'calibration': self.dataset.calibration, 'parameters': self.dataset.parameters}

        success = self.algorithm.initialize(cfg)

        if not success:
            return {'success': False, 'error': 'initialization failed'}

        for idx, frame in enumerate(self.dataset.frames):
            frame_data = FrameData(frame)
            pose_estimate = self.algorithm.process_frame(frame_data)

            if pose_estimate:
                self.poses.append(pose_estimate.pose)
                self.timestamps.append(pose_estimate.timestamp)

                if on_frame:
                    on_frame(idx, pose_estimate, frame_data)

        results = self.algorithm.finalize()

        self._save_results(results)

        return {'success': True, 'trajectory': results.trajectory.tolist(), 'num_poses': len(results.trajectory), 'output_dir': str(self.output_dir)}

    def _save_results(self, results):
        traj_file = self.output_dir / 'trajectory.txt'
        np.savetxt(traj_file, results.trajectory.reshape(-1, 16))

        results_file = self.output_dir / 'results.json'
        with open(results_file, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)

        if results.map_points is not None:
            map_file = self.output_dir / 'map.txt'
            np.savetxt(map_file, results.map_points)

class Dataset:
    def __init__(self, path, metadata=None):
        self.path = Path(path)
        self.metadata = metadata if metadata is not None else {}
        self.frames = []
        self.calibration = {}
        self.parameters = {}
        self.ground_truth = None

    def load(self):
        metadata_file = self.path / 'metadata.json'

        if metadata_file.exists():
            with open(metadata_file) as f:
                self.metadata = json.load(f)

            self.frames = self.metadata.get('frames', [])
            self.calibration = self.metadata.get('calibration', {})

            if 'ground_truth' in self.metadata:
                self.ground_truth = np.array(self.metadata['ground_truth'])

        return self

    def set_parameters(self, params):
        self.parameters = params

def create_simple_algorithm(initialize_fn, process_fn, finalize_fn):
    class SimpleAlgorithm(SLAMAlgorithm):
        def __init__(self):
            self.init_fn = initialize_fn
            self.proc_fn = process_fn
            self.final_fn = finalize_fn
            self.state = {}

        def initialize(self, cfg):
            return self.init_fn(self.state, cfg)

        def process_frame(self, frame_data):
            return self.proc_fn(self.state, frame_data)

        def finalize(self):
            return self.final_fn(self.state)

    return SimpleAlgorithm()
