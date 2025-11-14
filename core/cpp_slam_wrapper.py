import subprocess
import numpy as np
import tempfile
import json
from pathlib import Path
import time
class CPPSLAMWrapper:
    def __init__(self, plugin_config):
        self.config = plugin_config
        self.wrapper_type = plugin_config.get('cpp_wrapper', {}).get('type', 'subprocess')
        self.slam_executable = None
        self.process = None
        self.temp_dir = None
        self.trajectory_file = None
        self.precomputed_trajectory = None
        self.current_frame_index = 0
    def initialize(self, params):
        wrapper_config = self.config.get('cpp_wrapper', {})
        if self.wrapper_type == 'subprocess':
            return self._initialize_subprocess(params, wrapper_config)
        elif self.wrapper_type == 'pybind11':
            return self._initialize_pybind11(params, wrapper_config)
        elif self.wrapper_type == 'ctypes':
            return self._initialize_ctypes(params, wrapper_config)
        else:
            return None, f'unsupported_wrapper_type_{self.wrapper_type}'
    def _initialize_subprocess(self, params, wrapper_config):
        executable_path = wrapper_config.get('executable')
        if not executable_path:
            return None, 'executable_path_not_specified'
        executable = Path(executable_path)
        if not executable.exists():
            return None, 'executable_not_found'
        self.slam_executable = executable
        self.temp_dir = Path(tempfile.mkdtemp(prefix='openslam_cpp_'))
        self.trajectory_file = self.temp_dir / 'trajectory.txt'
        args = wrapper_config.get('args', [])
        resolved_args = []
        for arg in args:
            arg_str = str(arg)
            arg_str = arg_str.replace('${TEMP_DIR}', str(self.temp_dir))
            arg_str = arg_str.replace('${TRAJECTORY_FILE}', str(self.trajectory_file))
            for key, value in params.items():
                arg_str = arg_str.replace(f'${{{key}}}', str(value))
            resolved_args.append(arg_str)
        state = {'executable': str(self.slam_executable), 'args': resolved_args, 'temp_dir': str(self.temp_dir), 'trajectory_file': str(self.trajectory_file), 'frame_count': 0}
        return state, None
    def _initialize_pybind11(self, params, wrapper_config):
        module_path = wrapper_config.get('module_path')
        if not module_path:
            return None, 'module_path_not_specified'
        import importlib.util
        spec = importlib.util.spec_from_file_location('cpp_slam_module', module_path)
        if spec is None or spec.loader is None:
            return None, 'module_load_failed'
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        class_name = wrapper_config.get('class_name', 'System')
        if not hasattr(module, class_name):
            return None, f'class_{class_name}_not_found'
        slam_class = getattr(module, class_name)
        init_args = []
        for arg_name in wrapper_config.get('init_args', []):
            if arg_name in params:
                init_args.append(params[arg_name])
        slam_instance = slam_class(*init_args)
        state = {'module': module, 'instance': slam_instance, 'frame_count': 0}
        return state, None
    def _initialize_ctypes(self, params, wrapper_config):
        return None, 'ctypes_not_implemented'
    def process_frame(self, state, frame_data, image_path=None):
        if self.wrapper_type == 'subprocess':
            return self._process_frame_subprocess(state, frame_data, image_path)
        elif self.wrapper_type == 'pybind11':
            return self._process_frame_pybind11(state, frame_data, image_path)
        else:
            return None, 'unsupported_wrapper_type'
    def _process_frame_subprocess(self, state, frame_data, image_path):
        state['frame_count'] += 1
        if image_path:
            image_list_file = Path(state['temp_dir']) / 'images.txt'
            with open(image_list_file, 'a') as f:
                timestamp = frame_data.get('timestamp', state['frame_count'])
                f.write(f'{timestamp} {image_path}\n')
        result = {'success': True, 'frame': state['frame_count']}
        return result, None
    def _process_frame_pybind11(self, state, frame_data, image_path):
        instance = state['instance']
        timestamp = frame_data.get('timestamp', 0.0)
        if not hasattr(instance, 'TrackMonocular'):
            return None, 'track_method_not_found'
        if image_path:
            import cv2
            image = cv2.imread(str(image_path))
            if image is None:
                return None, 'image_load_failed'
            pose = instance.TrackMonocular(image, timestamp)
        else:
            return None, 'image_required'
        state['frame_count'] += 1
        result = {'success': True, 'pose': pose, 'frame': state['frame_count']}
        return result, None
    def get_trajectory(self, state):
        if self.wrapper_type == 'subprocess':
            return self._get_trajectory_subprocess(state)
        elif self.wrapper_type == 'pybind11':
            return self._get_trajectory_pybind11(state)
        else:
            return None, 'unsupported_wrapper_type'
    def _get_trajectory_subprocess(self, state):
        trajectory_method = self.config.get('cpp_wrapper', {}).get('trajectory_extraction', 'file_based')
        if trajectory_method == 'file_based':
            trajectory_file = Path(state['trajectory_file'])
            if not trajectory_file.exists():
                return None, 'trajectory_file_not_found'
            trajectory = self._parse_trajectory_file(trajectory_file)
            if trajectory is None:
                return None, 'trajectory_parse_failed'
            return trajectory, None
        else:
            return None, 'unsupported_trajectory_method'
    def _get_trajectory_pybind11(self, state):
        instance = state['instance']
        if hasattr(instance, 'GetTrajectory'):
            trajectory = instance.GetTrajectory()
            return trajectory, None
        else:
            return None, 'get_trajectory_method_not_found'
    def _parse_trajectory_file(self, file_path):
        format_type = self.config.get('cpp_wrapper', {}).get('trajectory_format', 'tum')
        poses = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                values = line.strip().split()
                if format_type == 'tum':
                    if len(values) >= 8:
                        timestamp = float(values[0])
                        tx, ty, tz = float(values[1]), float(values[2]), float(values[3])
                        qx, qy, qz, qw = float(values[4]), float(values[5]), float(values[6]), float(values[7])
                        pose = self._quaternion_to_matrix(qw, qx, qy, qz, tx, ty, tz)
                        poses.append(pose)
                elif format_type == 'kitti':
                    if len(values) >= 12:
                        matrix = np.array([float(v) for v in values[:12]]).reshape(3, 4)
                        pose = np.eye(4)
                        pose[:3, :] = matrix
                        poses.append(pose)
        if len(poses) == 0:
            return None
        return np.array(poses)
    def _quaternion_to_matrix(self, qw, qx, qy, qz, x, y, z):
        norm = np.sqrt(qw**2 + qx**2 + qy**2 + qz**2)
        qw, qx, qy, qz = qw/norm, qx/norm, qy/norm, qz/norm
        R = np.array([[1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)], [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)], [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]])
        pose = np.eye(4)
        pose[:3, :3] = R
        pose[:3, 3] = [x, y, z]
        return pose
    def shutdown(self, state):
        if self.wrapper_type == 'subprocess':
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=10)
        return True, None
    def run_slam_process(self, state, image_dir, output_trajectory_file):
        if self.wrapper_type != 'subprocess':
            return None, 'only_subprocess_supported'
        cmd = [str(state['executable'])] + state['args']
        cmd_str = ' '.join(cmd)
        cmd_str = cmd_str.replace('${IMAGE_DIR}', str(image_dir))
        cmd_str = cmd_str.replace('${OUTPUT_TRAJECTORY}', str(output_trajectory_file))
        env = self.config.get('cpp_wrapper', {}).get('environment', {})
        process = subprocess.Popen(cmd_str, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=self.config.get('execution', {}).get('timeout', 300))
        if process.returncode != 0:
            return None, f'slam_process_failed_{process.returncode}'
        return {'stdout': stdout.decode('utf-8'), 'stderr': stderr.decode('utf-8'), 'returncode': process.returncode}, None
