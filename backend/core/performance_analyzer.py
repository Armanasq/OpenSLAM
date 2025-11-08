import sys
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
import io
import base64
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from shared.models import TrajectoryPoint, PerformanceMetrics
class TrajectoryErrorComputer:
    def __init__(self):
        self.ate_cache = {}
        self.rpe_cache = {}
    def compute_ate(self, estimated_trajectory: List[TrajectoryPoint], ground_truth_trajectory: List[TrajectoryPoint]) -> float:
        if len(estimated_trajectory) != len(ground_truth_trajectory):
            min_length = min(len(estimated_trajectory), len(ground_truth_trajectory))
            estimated_trajectory = estimated_trajectory[:min_length]
            ground_truth_trajectory = ground_truth_trajectory[:min_length]
        if len(estimated_trajectory) == 0:
            return float('inf')
        estimated_positions = np.array([point.position for point in estimated_trajectory])
        ground_truth_positions = np.array([point.position for point in ground_truth_trajectory])
        aligned_estimated = self._align_trajectories(estimated_positions, ground_truth_positions)
        squared_errors = np.sum((aligned_estimated - ground_truth_positions) ** 2, axis=1)
        ate = np.sqrt(np.mean(squared_errors))
        return ate
    def compute_rpe(self, estimated_trajectory: List[TrajectoryPoint], ground_truth_trajectory: List[TrajectoryPoint], delta: int = 1) -> Tuple[float, float]:
        if len(estimated_trajectory) < delta + 1 or len(ground_truth_trajectory) < delta + 1:
            return float('inf'), float('inf')
        min_length = min(len(estimated_trajectory), len(ground_truth_trajectory))
        estimated_trajectory = estimated_trajectory[:min_length]
        ground_truth_trajectory = ground_truth_trajectory[:min_length]
        trans_errors = []
        rot_errors = []
        for i in range(len(estimated_trajectory) - delta):
            est_pose1 = self._trajectory_point_to_matrix(estimated_trajectory[i])
            est_pose2 = self._trajectory_point_to_matrix(estimated_trajectory[i + delta])
            gt_pose1 = self._trajectory_point_to_matrix(ground_truth_trajectory[i])
            gt_pose2 = self._trajectory_point_to_matrix(ground_truth_trajectory[i + delta])
            est_relative = np.linalg.inv(est_pose1) @ est_pose2
            gt_relative = np.linalg.inv(gt_pose1) @ gt_pose2
            error_pose = np.linalg.inv(gt_relative) @ est_relative
            trans_error = np.linalg.norm(error_pose[:3, 3])
            rot_error = self._rotation_matrix_to_angle(error_pose[:3, :3])
            trans_errors.append(trans_error)
            rot_errors.append(rot_error)
        rpe_trans = np.sqrt(np.mean(np.array(trans_errors) ** 2))
        rpe_rot = np.sqrt(np.mean(np.array(rot_errors) ** 2))
        return rpe_trans, rpe_rot
    def _align_trajectories(self, estimated: np.ndarray, ground_truth: np.ndarray) -> np.ndarray:
        if len(estimated) != len(ground_truth):
            return estimated
        estimated_centered = estimated - np.mean(estimated, axis=0)
        ground_truth_centered = ground_truth - np.mean(ground_truth, axis=0)
        H = estimated_centered.T @ ground_truth_centered
        U, S, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T
        t = np.mean(ground_truth, axis=0) - R @ np.mean(estimated, axis=0)
        aligned = (R @ estimated.T).T + t
        return aligned
    def _trajectory_point_to_matrix(self, point: TrajectoryPoint) -> np.ndarray:
        matrix = np.eye(4)
        matrix[:3, 3] = point.position
        qx, qy, qz, qw = point.orientation
        matrix[:3, :3] = self._quaternion_to_rotation_matrix(qw, qx, qy, qz)
        return matrix
    def _quaternion_to_rotation_matrix(self, w: float, x: float, y: float, z: float) -> np.ndarray:
        R = np.array([
            [1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
            [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
            [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]
        ])
        return R
    def _rotation_matrix_to_angle(self, R: np.ndarray) -> float:
        trace = np.trace(R)
        angle = np.arccos(np.clip((trace - 1) / 2, -1, 1))
        return angle
    def compute_trajectory_statistics(self, trajectory: List[TrajectoryPoint]) -> Dict:
        if not trajectory:
            return {}
        positions = np.array([point.position for point in trajectory])
        distances = np.linalg.norm(np.diff(positions, axis=0), axis=1)
        total_distance = np.sum(distances)
        timestamps = [point.timestamp for point in trajectory]
        total_time = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0
        avg_speed = total_distance / total_time if total_time > 0 else 0
        return {'total_distance': total_distance, 'total_time': total_time, 'average_speed': avg_speed, 'num_poses': len(trajectory), 'start_position': positions[0].tolist(), 'end_position': positions[-1].tolist()}
class ErrorPlotGenerator:
    def __init__(self):
        plt.style.use('default')
    def generate_ate_plot(self, estimated_trajectory: List[TrajectoryPoint], ground_truth_trajectory: List[TrajectoryPoint]) -> str:
        if len(estimated_trajectory) != len(ground_truth_trajectory):
            min_length = min(len(estimated_trajectory), len(ground_truth_trajectory))
            estimated_trajectory = estimated_trajectory[:min_length]
            ground_truth_trajectory = ground_truth_trajectory[:min_length]
        errors = []
        for est, gt in zip(estimated_trajectory, ground_truth_trajectory):
            error = np.linalg.norm(np.array(est.position) - np.array(gt.position))
            errors.append(error)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        timestamps = [point.timestamp for point in estimated_trajectory]
        ax1.plot(timestamps, errors, 'b-', linewidth=2, label='ATE')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Error (m)')
        ax1.set_title('Absolute Trajectory Error over Time')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax2.hist(errors, bins=50, alpha=0.7, color='blue', edgecolor='black')
        ax2.set_xlabel('Error (m)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('ATE Distribution')
        ax2.grid(True, alpha=0.3)
        mean_error = np.mean(errors)
        std_error = np.std(errors)
        ax2.axvline(mean_error, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_error:.3f}m')
        ax2.axvline(mean_error + std_error, color='orange', linestyle='--', linewidth=1, label=f'±1σ: {std_error:.3f}m')
        ax2.axvline(mean_error - std_error, color='orange', linestyle='--', linewidth=1)
        ax2.legend()
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        return plot_data
    def generate_rpe_plot(self, estimated_trajectory: List[TrajectoryPoint], ground_truth_trajectory: List[TrajectoryPoint], delta: int = 1) -> str:
        computer = TrajectoryErrorComputer()
        min_length = min(len(estimated_trajectory), len(ground_truth_trajectory))
        estimated_trajectory = estimated_trajectory[:min_length]
        ground_truth_trajectory = ground_truth_trajectory[:min_length]
        trans_errors = []
        rot_errors = []
        timestamps = []
        for i in range(len(estimated_trajectory) - delta):
            est_pose1 = computer._trajectory_point_to_matrix(estimated_trajectory[i])
            est_pose2 = computer._trajectory_point_to_matrix(estimated_trajectory[i + delta])
            gt_pose1 = computer._trajectory_point_to_matrix(ground_truth_trajectory[i])
            gt_pose2 = computer._trajectory_point_to_matrix(ground_truth_trajectory[i + delta])
            est_relative = np.linalg.inv(est_pose1) @ est_pose2
            gt_relative = np.linalg.inv(gt_pose1) @ gt_pose2
            error_pose = np.linalg.inv(gt_relative) @ est_relative
            trans_error = np.linalg.norm(error_pose[:3, 3])
            rot_error = computer._rotation_matrix_to_angle(error_pose[:3, :3])
            trans_errors.append(trans_error)
            rot_errors.append(np.degrees(rot_error))
            timestamps.append(estimated_trajectory[i].timestamp)
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        ax1.plot(timestamps, trans_errors, 'b-', linewidth=2)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Translation Error (m)')
        ax1.set_title('RPE Translation Error over Time')
        ax1.grid(True, alpha=0.3)
        ax2.plot(timestamps, rot_errors, 'r-', linewidth=2)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Rotation Error (deg)')
        ax2.set_title('RPE Rotation Error over Time')
        ax2.grid(True, alpha=0.3)
        ax3.hist(trans_errors, bins=30, alpha=0.7, color='blue', edgecolor='black')
        ax3.set_xlabel('Translation Error (m)')
        ax3.set_ylabel('Frequency')
        ax3.set_title('RPE Translation Distribution')
        ax3.grid(True, alpha=0.3)
        ax4.hist(rot_errors, bins=30, alpha=0.7, color='red', edgecolor='black')
        ax4.set_xlabel('Rotation Error (deg)')
        ax4.set_ylabel('Frequency')
        ax4.set_title('RPE Rotation Distribution')
        ax4.grid(True, alpha=0.3)
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        return plot_data
    def generate_trajectory_comparison_plot(self, estimated_trajectory: List[TrajectoryPoint], ground_truth_trajectory: List[TrajectoryPoint]) -> str:
        est_positions = np.array([point.position for point in estimated_trajectory])
        gt_positions = np.array([point.position for point in ground_truth_trajectory])
        fig = plt.figure(figsize=(15, 5))
        ax1 = fig.add_subplot(131)
        ax1.plot(est_positions[:, 0], est_positions[:, 1], 'b-', linewidth=2, label='Estimated', alpha=0.8)
        ax1.plot(gt_positions[:, 0], gt_positions[:, 1], 'r-', linewidth=2, label='Ground Truth', alpha=0.8)
        ax1.set_xlabel('X (m)')
        ax1.set_ylabel('Y (m)')
        ax1.set_title('Top View (X-Y)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.axis('equal')
        ax2 = fig.add_subplot(132)
        ax2.plot(est_positions[:, 0], est_positions[:, 2], 'b-', linewidth=2, label='Estimated', alpha=0.8)
        ax2.plot(gt_positions[:, 0], gt_positions[:, 2], 'r-', linewidth=2, label='Ground Truth', alpha=0.8)
        ax2.set_xlabel('X (m)')
        ax2.set_ylabel('Z (m)')
        ax2.set_title('Side View (X-Z)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.axis('equal')
        ax3 = fig.add_subplot(133)
        ax3.plot(est_positions[:, 1], est_positions[:, 2], 'b-', linewidth=2, label='Estimated', alpha=0.8)
        ax3.plot(gt_positions[:, 1], gt_positions[:, 2], 'r-', linewidth=2, label='Ground Truth', alpha=0.8)
        ax3.set_xlabel('Y (m)')
        ax3.set_ylabel('Z (m)')
        ax3.set_title('Front View (Y-Z)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.axis('equal')
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        return plot_data
class PerformanceMetricsDisplay:
    def __init__(self):
        self.metrics_history = []
    def compute_metrics(self, estimated_trajectory: List[TrajectoryPoint], ground_truth_trajectory: List[TrajectoryPoint], execution_time: float, memory_usage: float) -> PerformanceMetrics:
        computer = TrajectoryErrorComputer()
        ate = computer.compute_ate(estimated_trajectory, ground_truth_trajectory)
        rpe_trans, rpe_rot = computer.compute_rpe(estimated_trajectory, ground_truth_trajectory)
        metrics = PerformanceMetrics(ate=ate, rpe_trans=rpe_trans, rpe_rot=rpe_rot, execution_time=execution_time, memory_usage=memory_usage)
        self.metrics_history.append(metrics)
        return metrics
    def generate_metrics_summary(self, metrics: PerformanceMetrics) -> Dict:
        return {'ate': {'value': metrics.ate, 'unit': 'm', 'description': 'Absolute Trajectory Error'}, 'rpe_translation': {'value': metrics.rpe_trans, 'unit': 'm', 'description': 'Relative Pose Error (Translation)'}, 'rpe_rotation': {'value': metrics.rpe_rot, 'unit': 'rad', 'description': 'Relative Pose Error (Rotation)'}, 'execution_time': {'value': metrics.execution_time, 'unit': 's', 'description': 'Algorithm Execution Time'}, 'memory_usage': {'value': metrics.memory_usage, 'unit': 'MB', 'description': 'Peak Memory Usage'}}
    def get_metrics_history(self) -> List[PerformanceMetrics]:
        return self.metrics_history.copy()
    def clear_history(self):
        self.metrics_history = []