#!/usr/bin/env python3
"""
DSO Algorithm Implementation
Direct Sparse Odometry
"""

import numpy as np
import cv2
from typing import Tuple, List, Dict, Any, Optional

class DSO:
    """
    Direct Sparse Odometry implementation
    """
    
    def __init__(self, photometric_threshold: float = 7.0, gradient_threshold: float = 8.0,
                 max_points: int = 2000, min_points: int = 500):
        """
        Initialize DSO algorithm
        
        Args:
            photometric_threshold: Photometric error threshold
            gradient_threshold: Gradient magnitude threshold
            max_points: Maximum number of points per frame
            min_points: Minimum number of points per frame
        """
        self.photometric_threshold = photometric_threshold
        self.gradient_threshold = gradient_threshold
        self.max_points = max_points
        self.min_points = min_points
        
        # Algorithm state
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        self.active_points = []
        self.frame_count = 0
        
        # Camera parameters (will be set during initialization)
        self.camera_matrix = None
        self.dist_coeffs = None
        
    def set_camera_parameters(self, camera_matrix: np.ndarray, dist_coeffs: np.ndarray):
        """
        Set camera calibration parameters
        
        Args:
            camera_matrix: 3x3 camera intrinsic matrix
            dist_coeffs: Distortion coefficients
        """
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        
    def select_pixels(self, image: np.ndarray) -> List[Tuple[int, int]]:
        """
        Select pixels with high gradients for tracking
        
        Args:
            image: Input grayscale image
            
        Returns:
            List of selected pixel coordinates
        """
        # Compute gradients
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Find pixels above gradient threshold
        candidates = np.where(gradient_magnitude > self.gradient_threshold)
        candidate_pixels = list(zip(candidates[1], candidates[0]))  # (x, y) format
        
        # Sort by gradient magnitude and select top candidates
        candidate_gradients = [gradient_magnitude[y, x] for x, y in candidate_pixels]
        sorted_candidates = [pixel for _, pixel in sorted(zip(candidate_gradients, candidate_pixels), reverse=True)]
        
        # Limit number of points
        selected_pixels = sorted_candidates[:min(len(sorted_candidates), self.max_points)]
        
        return selected_pixels
        
    def track_points(self, prev_image: np.ndarray, curr_image: np.ndarray, 
                    prev_points: List[Tuple[int, int]]) -> Tuple[List[Tuple[int, int]], List[float]]:
        """
        Track points between frames using optical flow
        
        Args:
            prev_image: Previous frame
            curr_image: Current frame
            prev_points: Points from previous frame
            
        Returns:
            Tracked points and photometric errors
        """
        if not prev_points:
            return [], []
            
        # Convert points to numpy array for OpenCV
        prev_pts = np.array(prev_points, dtype=np.float32).reshape(-1, 1, 2)
        
        # Use Lucas-Kanade optical flow
        curr_pts, status, error = cv2.calcOpticalFlowPyrLK(
            prev_image, curr_image, prev_pts, None,
            winSize=(15, 15),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
        )
        
        # Filter successful tracks
        good_points = []
        photometric_errors = []
        
        for i, (st, err) in enumerate(zip(status, error)):
            if st == 1:  # Successfully tracked
                curr_pt = tuple(curr_pts[i, 0])
                good_points.append(curr_pt)
                photometric_errors.append(err[0])
                
        return good_points, photometric_errors
        
    def estimate_pose(self, prev_points: List[Tuple[int, int]], 
                     curr_points: List[Tuple[int, int]]) -> np.ndarray:
        """
        Estimate camera pose from point correspondences
        
        Args:
            prev_points: Points from previous frame
            curr_points: Points from current frame
            
        Returns:
            4x4 transformation matrix
        """
        if len(prev_points) < 8 or self.camera_matrix is None:
            return np.eye(4)  # Return identity if insufficient points
            
        # Convert to numpy arrays
        pts1 = np.array(prev_points, dtype=np.float32)
        pts2 = np.array(curr_points, dtype=np.float32)
        
        # Estimate essential matrix
        E, mask = cv2.findEssentialMat(
            pts1, pts2, self.camera_matrix,
            method=cv2.RANSAC,
            prob=0.999,
            threshold=1.0
        )
        
        if E is None:
            return np.eye(4)
            
        # Recover pose from essential matrix
        _, R, t, _ = cv2.recoverPose(E, pts1, pts2, self.camera_matrix)
        
        # Create transformation matrix
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = t.flatten()
        
        return T
        
    def process_frame(self, image: np.ndarray, timestamp: float = None) -> Dict[str, Any]:
        """
        Process a single frame
        
        Args:
            image: Input grayscale image
            timestamp: Frame timestamp (optional)
            
        Returns:
            Processing results
        """
        self.frame_count += 1
        
        if self.frame_count == 1:
            # First frame - initialize
            self.prev_image = image.copy()
            self.active_points = self.select_pixels(image)
            
            result = {
                'pose': self.current_pose.copy(),
                'num_points': len(self.active_points),
                'tracking_quality': 1.0,
                'frame_id': self.frame_count
            }
        else:
            # Track points from previous frame
            tracked_points, photometric_errors = self.track_points(
                self.prev_image, image, self.active_points
            )
            
            # Filter points based on photometric error
            good_points = []
            good_prev_points = []
            
            for i, error in enumerate(photometric_errors):
                if error < self.photometric_threshold:
                    good_points.append(tracked_points[i])
                    good_prev_points.append(self.active_points[i])
                    
            # Estimate pose if we have enough good points
            if len(good_points) >= self.min_points:
                T = self.estimate_pose(good_prev_points, good_points)
                self.current_pose = self.current_pose @ T
                tracking_quality = len(good_points) / len(self.active_points) if self.active_points else 0
            else:
                tracking_quality = 0
                
            # Add new points if needed
            if len(good_points) < self.min_points:
                new_points = self.select_pixels(image)
                # Combine with existing good points
                self.active_points = good_points + new_points[:self.max_points - len(good_points)]
            else:
                self.active_points = good_points
                
            # Update previous frame
            self.prev_image = image.copy()
            
            # Add to trajectory
            self.trajectory.append(self.current_pose.copy())
            
            result = {
                'pose': self.current_pose.copy(),
                'num_points': len(self.active_points),
                'tracking_quality': tracking_quality,
                'frame_id': self.frame_count,
                'photometric_error': np.mean(photometric_errors) if photometric_errors else 0
            }
            
        return result
        
    def get_trajectory(self) -> List[np.ndarray]:
        """
        Get complete trajectory
        
        Returns:
            List of 4x4 pose matrices
        """
        return self.trajectory.copy()
        
    def get_active_points(self) -> List[Tuple[int, int]]:
        """
        Get currently active tracking points
        
        Returns:
            List of active point coordinates
        """
        return self.active_points.copy()
        
    def reset(self):
        """
        Reset algorithm state
        """
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        self.active_points = []
        self.frame_count = 0
        self.prev_image = None
        
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current algorithm parameters
        
        Returns:
            Parameter dictionary
        """
        return {
            'photometric_threshold': self.photometric_threshold,
            'gradient_threshold': self.gradient_threshold,
            'max_points': self.max_points,
            'min_points': self.min_points
        }
        
    def set_parameters(self, params: Dict[str, Any]):
        """
        Update algorithm parameters
        
        Args:
            params: Parameter dictionary
        """
        if 'photometric_threshold' in params:
            self.photometric_threshold = params['photometric_threshold']
        if 'gradient_threshold' in params:
            self.gradient_threshold = params['gradient_threshold']
        if 'max_points' in params:
            self.max_points = params['max_points']
        if 'min_points' in params:
            self.min_points = params['min_points']