#!/usr/bin/env python3

import numpy as np
from typing import Tuple, List, Dict, Any, Optional
import open3d as o3d

class LIOSAM:
    def __init__(self, voxel_size: float = 0.1, icp_threshold: float = 0.3,
                 loop_closure_radius: float = 15.0, keyframe_distance: float = 1.0):
        self.voxel_size = voxel_size
        self.icp_threshold = icp_threshold
        self.loop_closure_radius = loop_closure_radius
        self.keyframe_distance = keyframe_distance
        
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        self.frame_count = 0
        
        self.global_map = o3d.geometry.PointCloud()
        self.keyframes = []
        self.keyframe_poses = []
        
        self.imu_bias_accel = np.zeros(3)
        self.imu_bias_gyro = np.zeros(3)
        self.velocity = np.zeros(3)
        
    def preprocess_pointcloud(self, points: np.ndarray) -> o3d.geometry.PointCloud:
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
        pcd = pcd.voxel_down_sample(self.voxel_size)
        pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        
        return pcd
        
    def process_imu_preintegration(self, imu_data: List[Dict[str, Any]]) -> np.ndarray:
        delta_pose = np.eye(4)
        delta_velocity = np.zeros(3)
        
        for imu_sample in imu_data:
            accel = imu_sample.get('acceleration', np.zeros(3)) - self.imu_bias_accel
            gyro = imu_sample.get('angular_velocity', np.zeros(3)) - self.imu_bias_gyro
            dt = imu_sample.get('dt', 0.01)
            
            angle = np.linalg.norm(gyro) * dt
            if angle > 1e-8:
                axis = gyro / np.linalg.norm(gyro)
                K = np.array([[0, -axis[2], axis[1]],
                             [axis[2], 0, -axis[0]],
                             [-axis[1], axis[0], 0]])
                R_delta = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K
            else:
                R_delta = np.eye(3)
                
            delta_pose[:3, :3] = delta_pose[:3, :3] @ R_delta
            
            gravity = np.array([0, 0, -9.81])
            accel_world = delta_pose[:3, :3] @ accel + gravity
            
            delta_velocity += accel_world * dt
            delta_pose[:3, 3] += self.velocity * dt + 0.5 * accel_world * dt * dt
            self.velocity += accel_world * dt
            
        return delta_pose
        
    def scan_matching(self, source_pcd: o3d.geometry.PointCloud, 
                     target_pcd: o3d.geometry.PointCloud) -> Tuple[np.ndarray, float]:
        if len(target_pcd.points) == 0:
            return np.eye(4), 0.0
            
        reg_p2p = o3d.pipelines.registration.registration_icp(
            source_pcd, target_pcd,
            self.icp_threshold,
            np.eye(4),
            o3d.pipelines.registration.TransformationEstimationPointToPoint(),
            o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=50)
        )
        
        return reg_p2p.transformation, reg_p2p.fitness
        
    def detect_loop_closure(self, current_pose: np.ndarray) -> Optional[int]:
        current_position = current_pose[:3, 3]
        
        for i, keyframe_pose in enumerate(self.keyframe_poses):
            if i < len(self.keyframe_poses) - 10:
                keyframe_position = keyframe_pose[:3, 3]
                distance = np.linalg.norm(current_position - keyframe_position)
                
                if distance < self.loop_closure_radius:
                    return i
                    
        return None
        
    def add_keyframe(self, pose: np.ndarray, pointcloud: o3d.geometry.PointCloud):
        if len(self.keyframe_poses) == 0:
            self.keyframes.append(pointcloud)
            self.keyframe_poses.append(pose.copy())
            return True
            
        last_pose = self.keyframe_poses[-1]
        distance = np.linalg.norm(pose[:3, 3] - last_pose[:3, 3])
        
        if distance > self.keyframe_distance:
            self.keyframes.append(pointcloud)
            self.keyframe_poses.append(pose.copy())
            return True
            
        return False
        
    def factor_graph_optimization(self, loop_closure_idx: int):
        if loop_closure_idx is None:
            return
            
        loop_pose = self.keyframe_poses[loop_closure_idx]
        current_pose = self.current_pose
        
        pose_error = np.linalg.inv(loop_pose) @ current_pose
        
        correction_factor = 0.1
        correction = np.eye(4)
        correction[:3, 3] = pose_error[:3, 3] * correction_factor
        
        self.current_pose = self.current_pose @ np.linalg.inv(correction)
        
        for i in range(len(self.keyframe_poses) - 10, len(self.keyframe_poses)):
            if i >= 0:
                self.keyframe_poses[i] = self.keyframe_poses[i] @ np.linalg.inv(correction)
                
    def process_frame(self, pointcloud: np.ndarray, imu_data: List[Dict[str, Any]] = None,
                     gps_data: Dict[str, Any] = None, timestamp: float = None) -> Dict[str, Any]:
        self.frame_count += 1
        
        current_pcd = self.preprocess_pointcloud(pointcloud)
        
        if self.frame_count == 1:
            self.prev_pcd = current_pcd
            self.global_map = current_pcd
            self.add_keyframe(self.current_pose, current_pcd)
            
            result = {
                'pose': self.current_pose.copy(),
                'num_points': len(current_pcd.points),
                'scan_match_fitness': 1.0,
                'frame_id': self.frame_count,
                'is_keyframe': True
            }
        else:
            if imu_data is not None:
                imu_motion = self.process_imu_preintegration(imu_data)
                predicted_pose = self.current_pose @ imu_motion
            else:
                predicted_pose = self.current_pose
                
            transformation, fitness = self.scan_matching(current_pcd, self.prev_pcd)
            
            if fitness > 0.3:
                self.current_pose = predicted_pose @ transformation
            else:
                self.current_pose = predicted_pose
                
            loop_closure_idx = self.detect_loop_closure(self.current_pose)
            loop_closure_detected = loop_closure_idx is not None
            
            if loop_closure_detected:
                self.factor_graph_optimization(loop_closure_idx)
                
            current_pcd.transform(self.current_pose)
            self.global_map += current_pcd
            
            if self.frame_count % 5 == 0:
                self.global_map = self.global_map.voxel_down_sample(self.voxel_size)
                
            is_keyframe = self.add_keyframe(self.current_pose, current_pcd)
            
            self.prev_pcd = current_pcd
            
            if gps_data is not None:
                gps_position = gps_data.get('position', np.zeros(3))
                gps_covariance = gps_data.get('covariance', np.eye(3) * 100)
                
                if np.trace(gps_covariance) < 10:
                    gps_correction = gps_position - self.current_pose[:3, 3]
                    self.current_pose[:3, 3] += gps_correction * 0.1
                    
            self.trajectory.append(self.current_pose.copy())
            
            result = {
                'pose': self.current_pose.copy(),
                'num_points': len(current_pcd.points),
                'scan_match_fitness': fitness,
                'frame_id': self.frame_count,
                'is_keyframe': is_keyframe,
                'loop_closure_detected': loop_closure_detected,
                'loop_closure_id': loop_closure_idx,
                'num_keyframes': len(self.keyframes)
            }
            
        return result
        
    def get_trajectory(self) -> List[np.ndarray]:
        return self.trajectory.copy()
        
    def get_map(self) -> o3d.geometry.PointCloud:
        return self.global_map
        
    def get_keyframes(self) -> List[np.ndarray]:
        return self.keyframe_poses.copy()
        
    def reset(self):
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        self.frame_count = 0
        self.global_map = o3d.geometry.PointCloud()
        self.keyframes = []
        self.keyframe_poses = []
        self.imu_bias_accel = np.zeros(3)
        self.imu_bias_gyro = np.zeros(3)
        self.velocity = np.zeros(3)
        
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'voxel_size': self.voxel_size,
            'icp_threshold': self.icp_threshold,
            'loop_closure_radius': self.loop_closure_radius,
            'keyframe_distance': self.keyframe_distance
        }
        
    def set_parameters(self, params: Dict[str, Any]):
        if 'voxel_size' in params:
            self.voxel_size = params['voxel_size']
        if 'icp_threshold' in params:
            self.icp_threshold = params['icp_threshold']
        if 'loop_closure_radius' in params:
            self.loop_closure_radius = params['loop_closure_radius']
        if 'keyframe_distance' in params:
            self.keyframe_distance = params['keyframe_distance']