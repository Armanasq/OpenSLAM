#!/usr/bin/env python3
"""
RTAB-Map Algorithm Implementation
Real-Time Appearance-Based Mapping
"""

import numpy as np
import cv2
from typing import Tuple, List, Dict, Any, Optional
from sklearn.cluster import DBSCAN
import open3d as o3d

class RTABMap:
    """
    RTAB-Map implementation for RGB-D SLAM
    """
    
    def __init__(self, memory_threshold: int = 100, similarity_threshold: float = 0.2,
                 max_features: int = 400, depth_max: float = 4.0, voxel_size: float = 0.01):
        """
        Initialize RTAB-Map algorithm
        
        Args:
            memory_threshold: Maximum number of locations in working memory
            similarity_threshold: Loop closure similarity threshold
            max_features: Maximum number of features per image
            depth_max: Maximum depth for point cloud generation
            voxel_size: Voxel size for point cloud downsampling
        """
        self.memory_threshold = memory_threshold
        self.similarity_threshold = similarity_threshold
        self.max_features = max_features
        self.depth_max = depth_max
        self.voxel_size = voxel_size
        
        # Algorithm state
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        self.frame_count = 0
        
        # Memory management
        self.working_memory = []  # Recent locations
        self.long_term_memory = []  # All locations
        self.location_descriptors = []  # Visual descriptors for each location
        
        # Feature detector
        self.detector = cv2.ORB_create(nfeatures=self.max_features)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # Point cloud map
        self.global_map = o3d.geometry.PointCloud()
        
        # Camera parameters
        self.camera_matrix = None
        self.depth_scale = 1000.0  # Depth scale (mm to m)
        
    def set_camera_parameters(self, camera_matrix: np.ndarray, depth_scale: float = 1000.0):
        """
        Set camera calibration parameters
        
        Args:
            camera_matrix: 3x3 camera intrinsic matrix
            depth_scale: Depth scale factor (default: 1000 for mm to m)
        """
        self.camera_matrix = camera_matrix
        self.depth_scale = depth_scale
        
    def extract_features(self, image: np.ndarray) -> Tuple[List[cv2.KeyPoint], np.ndarray]:
        """
        Extract visual features from RGB image
        
        Args:
            image: RGB image
            
        Returns:
            Keypoints and descriptors
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
            
        # Detect and compute features
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        
        return keypoints, descriptors
        
    def create_point_cloud(self, rgb_image: np.ndarray, depth_image: np.ndarray) -> o3d.geometry.PointCloud:
        """
        Create point cloud from RGB-D data
        
        Args:
            rgb_image: RGB image
            depth_image: Depth image
            
        Returns:
            Point cloud
        """
        if self.camera_matrix is None:
            return o3d.geometry.PointCloud()
            
        height, width = depth_image.shape
        
        # Create coordinate grids
        u, v = np.meshgrid(np.arange(width), np.arange(height))
        
        # Convert depth to meters
        depth_m = depth_image.astype(np.float32) / self.depth_scale
        
        # Filter valid depths
        valid_mask = (depth_m > 0) & (depth_m < self.depth_max)
        
        # Get camera intrinsics
        fx, fy = self.camera_matrix[0, 0], self.camera_matrix[1, 1]
        cx, cy = self.camera_matrix[0, 2], self.camera_matrix[1, 2]
        
        # Back-project to 3D
        x = (u - cx) * depth_m / fx
        y = (v - cy) * depth_m / fy
        z = depth_m
        
        # Filter valid points
        valid_points = valid_mask.flatten()
        points_3d = np.stack([x.flatten(), y.flatten(), z.flatten()], axis=1)[valid_points]
        
        # Get corresponding colors
        if len(rgb_image.shape) == 3:
            colors = rgb_image.reshape(-1, 3)[valid_points] / 255.0
        else:
            colors = np.tile(rgb_image.flatten()[valid_points][:, None], (1, 3)) / 255.0
            
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points_3d)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        # Downsample
        if self.voxel_size > 0:
            pcd = pcd.voxel_down_sample(self.voxel_size)
            
        return pcd
        
    def compute_similarity(self, desc1: np.ndarray, desc2: np.ndarray) -> float:
        """
        Compute similarity between two descriptor sets
        
        Args:
            desc1: First descriptor set
            desc2: Second descriptor set
            
        Returns:
            Similarity score (0-1)
        """
        if desc1 is None or desc2 is None or len(desc1) == 0 or len(desc2) == 0:
            return 0.0
            
        # Match descriptors
        matches = self.matcher.match(desc1, desc2)
        
        if len(matches) == 0:
            return 0.0
            
        # Sort matches by distance
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Compute similarity based on good matches
        good_matches = [m for m in matches if m.distance < 50]  # Threshold for good matches
        similarity = len(good_matches) / min(len(desc1), len(desc2))
        
        return min(similarity, 1.0)
        
    def detect_loop_closure(self, current_descriptors: np.ndarray) -> Optional[int]:
        """
        Detect loop closure with previous locations
        
        Args:
            current_descriptors: Current frame descriptors
            
        Returns:
            Index of loop closure location (if detected)
        """
        best_similarity = 0.0
        best_location = None
        
        # Check similarity with locations in long-term memory
        for i, descriptors in enumerate(self.location_descriptors):
            if i < len(self.location_descriptors) - 10:  # Skip recent locations
                similarity = self.compute_similarity(current_descriptors, descriptors)
                
                if similarity > best_similarity and similarity > self.similarity_threshold:
                    best_similarity = similarity
                    best_location = i
                    
        return best_location
        
    def update_memory(self, location_data: Dict[str, Any]):
        """
        Update working and long-term memory
        
        Args:
            location_data: Current location data
        """
        # Add to long-term memory
        self.long_term_memory.append(location_data)
        
        # Add to working memory
        self.working_memory.append(location_data)
        
        # Manage working memory size
        if len(self.working_memory) > self.memory_threshold:
            # Remove oldest location from working memory
            self.working_memory.pop(0)
            
    def estimate_pose(self, prev_keypoints: List[cv2.KeyPoint], curr_keypoints: List[cv2.KeyPoint],
                     prev_descriptors: np.ndarray, curr_descriptors: np.ndarray) -> np.ndarray:
        """
        Estimate camera pose from feature matches
        
        Args:
            prev_keypoints: Previous frame keypoints
            curr_keypoints: Current frame keypoints
            prev_descriptors: Previous frame descriptors
            curr_descriptors: Current frame descriptors
            
        Returns:
            4x4 transformation matrix
        """
        if prev_descriptors is None or curr_descriptors is None:
            return np.eye(4)
            
        # Match features
        matches = self.matcher.match(prev_descriptors, curr_descriptors)
        
        if len(matches) < 8:  # Need minimum matches for pose estimation
            return np.eye(4)
            
        # Extract matched points
        prev_pts = np.array([prev_keypoints[m.queryIdx].pt for m in matches], dtype=np.float32)
        curr_pts = np.array([curr_keypoints[m.trainIdx].pt for m in matches], dtype=np.float32)
        
        # Estimate essential matrix
        if self.camera_matrix is not None:
            E, mask = cv2.findEssentialMat(
                prev_pts, curr_pts, self.camera_matrix,
                method=cv2.RANSAC, prob=0.999, threshold=1.0
            )
            
            if E is not None:
                # Recover pose
                _, R, t, _ = cv2.recoverPose(E, prev_pts, curr_pts, self.camera_matrix)
                
                # Create transformation matrix
                T = np.eye(4)
                T[:3, :3] = R
                T[:3, 3] = t.flatten()
                
                return T
                
        return np.eye(4)
        
    def process_frame(self, rgb_image: np.ndarray, depth_image: np.ndarray, 
                     timestamp: float = None) -> Dict[str, Any]:
        """
        Process RGB-D frame
        
        Args:
            rgb_image: RGB image
            depth_image: Depth image
            timestamp: Frame timestamp (optional)
            
        Returns:
            Processing results
        """
        self.frame_count += 1
        
        # Extract features
        keypoints, descriptors = self.extract_features(rgb_image)
        
        # Create point cloud
        point_cloud = self.create_point_cloud(rgb_image, depth_image)
        
        # Initialize or update pose
        if self.frame_count == 1:
            # First frame
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            loop_closure_detected = False
            loop_closure_id = None
            
        else:
            # Estimate pose from previous frame
            T = self.estimate_pose(self.prev_keypoints, keypoints, 
                                 self.prev_descriptors, descriptors)
            self.current_pose = self.current_pose @ T
            
            # Detect loop closure
            loop_closure_id = self.detect_loop_closure(descriptors)
            loop_closure_detected = loop_closure_id is not None
            
            # Update previous frame data
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            
        # Transform point cloud to global frame
        if len(point_cloud.points) > 0:
            point_cloud.transform(self.current_pose)
            self.global_map += point_cloud
            
            # Downsample global map periodically
            if self.frame_count % 10 == 0:
                self.global_map = self.global_map.voxel_down_sample(self.voxel_size)
                
        # Create location data
        location_data = {
            'pose': self.current_pose.copy(),
            'keypoints': keypoints,
            'descriptors': descriptors,
            'point_cloud': point_cloud,
            'timestamp': timestamp,
            'frame_id': self.frame_count
        }
        
        # Update memory
        self.update_memory(location_data)
        self.location_descriptors.append(descriptors)
        
        # Add to trajectory
        self.trajectory.append(self.current_pose.copy())
        
        # Prepare results
        result = {
            'pose': self.current_pose.copy(),
            'num_features': len(keypoints),
            'num_points': len(point_cloud.points),
            'loop_closure_detected': loop_closure_detected,
            'loop_closure_id': loop_closure_id,
            'frame_id': self.frame_count,
            'memory_usage': len(self.working_memory)
        }
        
        return result
        
    def get_trajectory(self) -> List[np.ndarray]:
        """Get complete trajectory"""
        return self.trajectory.copy()
        
    def get_map(self) -> o3d.geometry.PointCloud:
        """Get global point cloud map"""
        return self.global_map
        
    def get_memory_locations(self) -> List[Dict[str, Any]]:
        """Get all memory locations"""
        return self.long_term_memory.copy()
        
    def reset(self):
        """Reset algorithm state"""
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        self.frame_count = 0
        self.working_memory = []
        self.long_term_memory = []
        self.location_descriptors = []
        self.global_map = o3d.geometry.PointCloud()
        
    def get_parameters(self) -> Dict[str, Any]:
        """Get current algorithm parameters"""
        return {
            'memory_threshold': self.memory_threshold,
            'similarity_threshold': self.similarity_threshold,
            'max_features': self.max_features,
            'depth_max': self.depth_max,
            'voxel_size': self.voxel_size
        }
        
    def set_parameters(self, params: Dict[str, Any]):
        """Update algorithm parameters"""
        if 'memory_threshold' in params:
            self.memory_threshold = params['memory_threshold']
        if 'similarity_threshold' in params:
            self.similarity_threshold = params['similarity_threshold']
        if 'max_features' in params:
            self.max_features = params['max_features']
            self.detector = cv2.ORB_create(nfeatures=self.max_features)
        if 'depth_max' in params:
            self.depth_max = params['depth_max']
        if 'voxel_size' in params:
            self.voxel_size = params['voxel_size']