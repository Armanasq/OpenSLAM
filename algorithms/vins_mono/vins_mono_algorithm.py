#!/usr/bin/env python3

import numpy as np
import cv2
from typing import Tuple, List, Dict, Any, Optional

class VINSMono:
    def __init__(self, max_features: int = 150, min_distance: int = 30, 
                 focal_length: float = 460, loop_closure_threshold: float = 0.3):
        self.max_features = max_features
        self.min_distance = min_distance
        self.focal_length = focal_length
        self.loop_closure_threshold = loop_closure_threshold
        
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        self.frame_count = 0
        
        self.detector = cv2.goodFeaturesToTrack
        self.tracker = cv2.calcOpticalFlowPyrLK
        
        self.camera_matrix = None
        self.dist_coeffs = None
        
    def set_camera_parameters(self, camera_matrix: np.ndarray, dist_coeffs: np.ndarray):
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        
    def detect_features(self, image: np.ndarray) -> np.ndarray:
        corners = cv2.goodFeaturesToTrack(
            image,
            maxCorners=self.max_features,
            qualityLevel=0.01,
            minDistance=self.min_distance,
            blockSize=3
        )
        
        return corners if corners is not None else np.array([])
        
    def track_features(self, prev_image: np.ndarray, curr_image: np.ndarray, 
                      prev_points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if len(prev_points) == 0:
            return np.array([]), np.array([])
            
        next_points, status, error = cv2.calcOpticalFlowPyrLK(
            prev_image, curr_image, prev_points, None,
            winSize=(21, 21),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        )
        
        good_new = next_points[status == 1]
        good_old = prev_points[status == 1]
        
        return good_old, good_new
        
    def estimate_pose_pnp(self, points_3d: np.ndarray, points_2d: np.ndarray) -> np.ndarray:
        if len(points_3d) < 4 or self.camera_matrix is None:
            return np.eye(4)
            
        success, rvec, tvec, inliers = cv2.solvePnPRansac(
            points_3d, points_2d, self.camera_matrix, self.dist_coeffs
        )
        
        if success:
            R, _ = cv2.Rodrigues(rvec)
            T = np.eye(4)
            T[:3, :3] = R
            T[:3, 3] = tvec.flatten()
            return T
            
        return np.eye(4)
        
    def triangulate_points(self, points1: np.ndarray, points2: np.ndarray, 
                          pose1: np.ndarray, pose2: np.ndarray) -> np.ndarray:
        if self.camera_matrix is None or len(points1) == 0:
            return np.array([])
            
        P1 = self.camera_matrix @ pose1[:3, :]
        P2 = self.camera_matrix @ pose2[:3, :]
        
        points_4d = cv2.triangulatePoints(P1, P2, points1.T, points2.T)
        points_3d = points_4d[:3] / points_4d[3]
        
        return points_3d.T
        
    def process_imu(self, imu_data: Dict[str, np.ndarray]) -> np.ndarray:
        accel = imu_data.get('acceleration', np.zeros(3))
        gyro = imu_data.get('angular_velocity', np.zeros(3))
        
        dt = imu_data.get('dt', 0.01)
        
        rotation_delta = gyro * dt
        angle = np.linalg.norm(rotation_delta)
        
        if angle > 1e-8:
            axis = rotation_delta / angle
            K = np.array([[0, -axis[2], axis[1]],
                         [axis[2], 0, -axis[0]],
                         [-axis[1], axis[0], 0]])
            R_delta = np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K
        else:
            R_delta = np.eye(3)
            
        T_delta = np.eye(4)
        T_delta[:3, :3] = R_delta
        T_delta[:3, 3] = accel * dt * dt * 0.5
        
        return T_delta
        
    def process_frame(self, image: np.ndarray, imu_data: Dict[str, np.ndarray] = None, 
                     timestamp: float = None) -> Dict[str, Any]:
        self.frame_count += 1
        
        if self.frame_count == 1:
            self.prev_image = image.copy()
            self.prev_points = self.detect_features(image)
            self.landmarks_3d = np.array([])
            
            result = {
                'pose': self.current_pose.copy(),
                'num_features': len(self.prev_points),
                'tracking_quality': 1.0,
                'frame_id': self.frame_count
            }
        else:
            if imu_data is not None:
                imu_motion = self.process_imu(imu_data)
                self.current_pose = self.current_pose @ imu_motion
                
            if len(self.prev_points) > 0:
                old_points, new_points = self.track_features(
                    self.prev_image, image, self.prev_points
                )
                
                if len(new_points) >= 8:
                    if len(self.landmarks_3d) >= len(old_points):
                        matched_3d = self.landmarks_3d[:len(old_points)]
                        T = self.estimate_pose_pnp(matched_3d, new_points)
                        self.current_pose = T
                    else:
                        if self.camera_matrix is not None:
                            E, mask = cv2.findEssentialMat(
                                old_points, new_points, self.camera_matrix
                            )
                            if E is not None:
                                _, R, t, _ = cv2.recoverPose(
                                    E, old_points, new_points, self.camera_matrix
                                )
                                T = np.eye(4)
                                T[:3, :3] = R
                                T[:3, 3] = t.flatten()
                                self.current_pose = self.current_pose @ T
                                
                                new_landmarks = self.triangulate_points(
                                    old_points, new_points, 
                                    np.eye(4), T
                                )
                                if len(new_landmarks) > 0:
                                    self.landmarks_3d = new_landmarks
                    
                    tracking_quality = len(new_points) / len(self.prev_points)
                else:
                    tracking_quality = 0
                    new_points = self.detect_features(image)
            else:
                new_points = self.detect_features(image)
                tracking_quality = 0
                
            self.prev_image = image.copy()
            self.prev_points = new_points
            
            self.trajectory.append(self.current_pose.copy())
            
            result = {
                'pose': self.current_pose.copy(),
                'num_features': len(new_points),
                'tracking_quality': tracking_quality,
                'frame_id': self.frame_count,
                'num_landmarks': len(self.landmarks_3d)
            }
            
        return result
        
    def get_trajectory(self) -> List[np.ndarray]:
        return self.trajectory.copy()
        
    def get_landmarks(self) -> np.ndarray:
        return self.landmarks_3d.copy() if hasattr(self, 'landmarks_3d') else np.array([])
        
    def reset(self):
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        self.frame_count = 0
        self.prev_image = None
        self.prev_points = np.array([])
        self.landmarks_3d = np.array([])
        
    def get_parameters(self) -> Dict[str, Any]:
        return {
            'max_features': self.max_features,
            'min_distance': self.min_distance,
            'focal_length': self.focal_length,
            'loop_closure_threshold': self.loop_closure_threshold
        }
        
    def set_parameters(self, params: Dict[str, Any]):
        if 'max_features' in params:
            self.max_features = params['max_features']
        if 'min_distance' in params:
            self.min_distance = params['min_distance']
        if 'focal_length' in params:
            self.focal_length = params['focal_length']
        if 'loop_closure_threshold' in params:
            self.loop_closure_threshold = params['loop_closure_threshold']