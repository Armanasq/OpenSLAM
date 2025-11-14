import numpy as np
import time
from pathlib import Path
import plugin_config as pcfg
from core.plugin_manager import PluginManager
from core import dataset_loader, metrics
from core.cpp_slam_wrapper import CPPSLAMWrapper
from core.workflow_executor import WorkflowExecutor
class PluginExecutor:
    def __init__(self, plugin_name):
        self.plugin_name = plugin_name
        self.plugin_manager = PluginManager()
        self.plugin = None
        self.state = {}
        self.trajectory = []
        self.timestamps = []
        self.processing_times = []
        self.is_cpp_plugin = False
        self.cpp_wrapper = None
        self.is_workflow_plugin = False
        self.workflow_executor = None
    def load(self):
        plugin, error = self.plugin_manager.load_plugin(self.plugin_name)
        if error:
            return None, error
        self.plugin = plugin
        plugin_config = plugin['config']
        if 'workflow' in plugin_config or 'interface' in plugin_config:
            self.is_workflow_plugin = True
            self.workflow_executor = WorkflowExecutor()
        elif plugin_config.get('language') == 'cpp':
            self.is_cpp_plugin = True
            self.cpp_wrapper = CPPSLAMWrapper(plugin_config)
        return plugin, None
    def initialize(self, config_params=None):
        if self.plugin is None:
            return None, 'plugin_not_loaded'
        plugin_config = self.plugin['config']
        if config_params is None:
            config_params = plugin_config.get('default_params', {})
        if self.is_cpp_plugin:
            state, error = self.cpp_wrapper.initialize(config_params)
            if error:
                return None, error
            self.state = state if state else {}
            return self.state, None
        init_func, error = self.plugin_manager.get_plugin_function(self.plugin, 'initialize')
        if error:
            return None, error
        result = init_func(config_params)
        if isinstance(result, tuple) and len(result) == 2:
            state, error = result
            if error:
                return None, error
            self.state = state if state else {}
        else:
            self.state = result if result else {}
        return self.state, None
    def process_frame(self, frame_data, image_path=None):
        if self.plugin is None:
            return None, 'plugin_not_loaded'
        start_time = time.time()
        if self.is_cpp_plugin:
            result, error = self.cpp_wrapper.process_frame(self.state, frame_data, image_path)
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            if error:
                return None, error
            return result, None
        process_func, error = self.plugin_manager.get_plugin_function(self.plugin, 'process_frame')
        if error:
            return None, error
        result = process_func(self.state, frame_data)
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        if processing_time > pcfg.MAX_FRAME_PROCESSING_TIME:
            return None, f'frame_timeout_{processing_time:.2f}s'
        if isinstance(result, tuple) and len(result) == 2:
            output, error = result
            if error:
                return None, error
            return output, None
        return result, None
    def get_current_pose(self):
        if self.plugin is None:
            return None, 'plugin_not_loaded'
        if self.is_cpp_plugin:
            if 'current_pose' in self.state:
                return self.state['current_pose'], None
            return None, 'pose_not_available'
        get_pose_func, error = self.plugin_manager.get_plugin_function(self.plugin, 'get_current_pose')
        if error:
            return None, error
        result = get_pose_func(self.state)
        if isinstance(result, tuple) and len(result) == 2:
            pose, error = result
            if error:
                return None, error
            return pose, None
        return result, None
    def get_full_trajectory(self):
        if self.plugin is None:
            return None, 'plugin_not_loaded'
        if self.is_cpp_plugin:
            trajectory, error = self.cpp_wrapper.get_trajectory(self.state)
            if error:
                if len(self.trajectory) > 0:
                    return np.array(self.trajectory), None
                return None, error
            return trajectory, None
        get_traj_func, error = self.plugin_manager.get_plugin_function(self.plugin, 'get_full_trajectory')
        if error:
            if len(self.trajectory) > 0:
                return np.array(self.trajectory), None
            return None, error
        result = get_traj_func(self.state)
        if isinstance(result, tuple) and len(result) == 2:
            trajectory, error = result
            if error:
                return None, error
            return trajectory, None
        return result, None
    def shutdown(self):
        if self.plugin is None:
            return None, 'plugin_not_loaded'
        if self.is_cpp_plugin:
            return self.cpp_wrapper.shutdown(self.state)
        shutdown_func, error = self.plugin_manager.get_plugin_function(self.plugin, 'shutdown')
        if error:
            return True, None
        result = shutdown_func(self.state)
        if isinstance(result, tuple):
            return result
        return True, None
    def _run_workflow(self, dataset_path, dataset_format):
        plugin_config = self.plugin['config']
        output_dir = Path(f'results/{self.plugin_name}')
        result, error = self.workflow_executor.execute_workflow(plugin_config, dataset_path, str(output_dir))
        if error:
            return None, error
        trajectory = result.get('trajectory')
        if trajectory is None:
            return None, 'no_trajectory_in_workflow_result'
        if isinstance(trajectory, dict):
            if 'poses' in trajectory:
                poses = trajectory['poses']
                timestamps = trajectory.get('timestamps')
            else:
                return None, 'trajectory_dict_missing_poses'
        else:
            poses = trajectory
            timestamps = None
        if not isinstance(poses, np.ndarray):
            poses = np.array(poses)
        result_dict = {'trajectory': poses, 'timestamps': timestamps, 'processing_times': [], 'frames_processed': len(poses), 'total_frames': len(poses)}
        return result_dict, None
    def run_on_dataset(self, dataset_path, dataset_format=None):
        load_result, error = self.load()
        if error:
            return None, error
        if self.is_workflow_plugin:
            return self._run_workflow(dataset_path, dataset_format)
        dataset, error = dataset_loader.load_dataset(dataset_path, format_type=dataset_format)
        if error:
            return None, error
        adapter, error = self.get_data_adapter(dataset)
        if error:
            return None, error
        init_result, error = self.initialize()
        if error:
            return None, error
        if 'sequences' in dataset:
            poses_data = dataset['sequences'][0]['poses']
            timestamps_data = dataset['sequences'][0]['timestamps']
        else:
            poses_data = dataset['poses']
            timestamps_data = dataset['timestamps']
        self.trajectory = []
        self.timestamps = []
        self.processing_times = []
        frame_count = len(poses_data)
        for i in range(frame_count):
            frame_data = adapter.get_frame_data(i)
            if frame_data is None:
                continue
            process_result, error = self.process_frame(frame_data)
            if error:
                continue
            pose, error = self.get_current_pose()
            if error:
                continue
            if timestamps_data is not None:
                timestamp = timestamps_data[i]
            else:
                timestamp = float(i)
            self.trajectory.append(pose)
            self.timestamps.append(timestamp)
        shutdown_result, error = self.shutdown()
        if len(self.trajectory) == 0:
            return None, 'no_trajectory_generated'
        trajectory_array = np.array(self.trajectory)
        result = {'trajectory': trajectory_array, 'timestamps': np.array(self.timestamps) if len(self.timestamps) > 0 else None, 'processing_times': self.processing_times, 'frames_processed': len(self.trajectory), 'total_frames': frame_count}
        return result, None
    def get_data_adapter(self, dataset):
        dataset_format = dataset.get('format', 'custom')
        adapter, error = self.plugin_manager.get_data_adapter(self.plugin, dataset_format, dataset)
        if error:
            return DefaultDataAdapter(dataset), None
        return adapter, None
    def evaluate_on_dataset(self, dataset_path, ground_truth_path, dataset_format=None):
        result, error = self.run_on_dataset(dataset_path, dataset_format=dataset_format)
        if error:
            return None, error
        gt_dataset, error = dataset_loader.load_dataset(ground_truth_path, format_type=dataset_format)
        if error:
            return None, error
        if 'sequences' in gt_dataset:
            gt_poses = gt_dataset['sequences'][0]['poses']
        else:
            gt_poses = gt_dataset['poses']
        estimated_poses = result['trajectory']
        eval_results, error = metrics.evaluate_trajectory(estimated_poses, gt_poses)
        if error:
            return None, error
        eval_results['plugin_name'] = self.plugin_name
        eval_results['processing_times'] = result['processing_times']
        eval_results['avg_processing_time'] = float(np.mean(result['processing_times']))
        eval_results['frames_processed'] = result['frames_processed']
        eval_results['total_frames'] = result['total_frames']
        return eval_results, None
class DefaultDataAdapter:
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
        return frame_data
