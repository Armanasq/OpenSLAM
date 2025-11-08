import sys
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from abc import ABC, abstractmethod
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
class MonocularDepthEstimator(ABC):
    def __init__(self, camera_matrix: np.ndarray):
        self.camera_matrix = camera_matrix
        self.focal_length = camera_matrix[0, 0]
        self.cx = camera_matrix[0, 2]
        self.cy = camera_matrix[1, 2]
    @abstractmethod
    def estimate_depth(self, image: np.ndarray, **kwargs) -> np.ndarray:
        pass
    @abstractmethod
    def get_estimator_params(self) -> Dict:
        pass
class StructureFromMotionDepth(MonocularDepthEstimator):
    def __init__(self, camera_matrix: np.ndarray, feature_detector: str = 'ORB', min_features: int = 100):
        super().__init__(camera_matrix)
        self.feature_detector_type = feature_detector
        self.min_features = min_features
        self.previous_frame = None
        self.previous_keypoints = None
        self.previous_descriptors = None
        self.accumulated_pose = np.eye(4)
        self.landmark_map = {}
        self._setup_feature_detector()
    def _setup_feature_detector(self):
        if self.feature_detector_type == 'ORB':
            self.detector = cv2.ORB_create(nfeatures=1000)
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        elif self.feature_detector_type == 'SIFT':
            self.detector = cv2.SIFT_create(nfeatures=1000)
            self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        else:
            raise ValueError(f"Unsupported feature detector: {self.feature_detector_type}")
    def estimate_depth(self, image: np.ndarray, **kwargs) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        depth_map = np.zeros(gray.shape, dtype=np.float32)
        if self.previous_descriptors is not None and descriptors is not None:
            matches = self.matcher.match(self.previous_descriptors, descriptors)
            matches = sorted(matches, key=lambda x: x.distance)
            if len(matches) >= self.min_features:
                pts1 = np.float32([self.previous_keypoints[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
                pts2 = np.float32([keypoints[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
                E, mask = cv2.findEssentialMat(pts1, pts2, self.camera_matrix, method=cv2.RANSAC, prob=0.999, threshold=1.0)
                if E is not None:
                    retval, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, self.camera_matrix, mask=mask)
                    if retval > 0:
                        inlier_pts1 = pts1[mask.ravel().astype(bool)]
                        inlier_pts2 = pts2[mask.ravel().astype(bool)]
                        depths = self._triangulate_points(inlier_pts1, inlier_pts2, R, t)
                        for i, (pt, depth) in enumerate(zip(inlier_pts2, depths)):
                            if depth > 0 and depth < 100:
                                x, y = int(pt[0][0]), int(pt[0][1])
                                if 0 <= x < depth_map.shape[1] and 0 <= y < depth_map.shape[0]:
                                    depth_map[y, x] = depth
                        self.accumulated_pose = self.accumulated_pose @ np.vstack([np.hstack([R, t]), [0, 0, 0, 1]])
        self.previous_frame = gray
        self.previous_keypoints = keypoints
        self.previous_descriptors = descriptors
        return self._interpolate_sparse_depth(depth_map)
    def _triangulate_points(self, pts1: np.ndarray, pts2: np.ndarray, R: np.ndarray, t: np.ndarray) -> np.ndarray:
        P1 = self.camera_matrix @ np.hstack([np.eye(3), np.zeros((3, 1))])
        P2 = self.camera_matrix @ np.hstack([R, t])
        pts1_norm = pts1.reshape(-1, 2).T
        pts2_norm = pts2.reshape(-1, 2).T
        points_4d = cv2.triangulatePoints(P1, P2, pts1_norm, pts2_norm)
        points_3d = points_4d[:3] / points_4d[3]
        depths = points_3d[2]
        return depths
    def _interpolate_sparse_depth(self, sparse_depth: np.ndarray) -> np.ndarray:
        valid_mask = sparse_depth > 0
        if np.sum(valid_mask) < 4:
            return sparse_depth
        try:
            from scipy import interpolate
            height, width = sparse_depth.shape
            y, x = np.mgrid[0:height, 0:width]
            valid_points = np.column_stack([x[valid_mask], y[valid_mask]])
            valid_values = sparse_depth[valid_mask]
            interp = interpolate.griddata(valid_points, valid_values, (x, y), method='linear', fill_value=0)
            return interp
        except ImportError:
            return sparse_depth
    def get_estimator_params(self) -> Dict:
        return {'type': 'StructureFromMotion', 'feature_detector': self.feature_detector_type, 'min_features': self.min_features}
    def reset(self):
        self.previous_frame = None
        self.previous_keypoints = None
        self.previous_descriptors = None
        self.accumulated_pose = np.eye(4)
        self.landmark_map = {}
class LearningBasedDepthEstimator(MonocularDepthEstimator):
    def __init__(self, camera_matrix: np.ndarray, model_type: str = 'midas', model_path: Optional[str] = None):
        super().__init__(camera_matrix)
        self.model_type = model_type
        self.model_path = model_path
        self.model = None
        self.transform = None
        self._load_model()
    def _load_model(self):
        if self.model_type == 'midas':
            try:
                import torch
                self.model = torch.hub.load('intel-isl/MiDaS', 'MiDaS')
                self.model.eval()
                midas_transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
                self.transform = midas_transforms.default_transform
                self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                self.model.to(self.device)
            except ImportError:
                raise ImportError("PyTorch is required for MiDaS depth estimation")
        elif self.model_type == 'dpt':
            try:
                import torch
                self.model = torch.hub.load('intel-isl/MiDaS', 'DPT_Large')
                self.model.eval()
                midas_transforms = torch.hub.load('intel-isl/MiDaS', 'transforms')
                self.transform = midas_transforms.dpt_transform
                self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                self.model.to(self.device)
            except ImportError:
                raise ImportError("PyTorch is required for DPT depth estimation")
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    def estimate_depth(self, image: np.ndarray, **kwargs) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Model not loaded")
        try:
            import torch
            if len(image.shape) == 2:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            input_tensor = self.transform(image_rgb).to(self.device)
            with torch.no_grad():
                prediction = self.model(input_tensor)
                prediction = torch.nn.functional.interpolate(prediction.unsqueeze(1), size=image.shape[:2], mode='bicubic', align_corners=False).squeeze()
            depth_map = prediction.cpu().numpy()
            depth_map = self._normalize_depth(depth_map)
            return depth_map
        except Exception as e:
            raise RuntimeError(f"Depth estimation failed: {str(e)}")
    def _normalize_depth(self, depth_map: np.ndarray) -> np.ndarray:
        depth_min = depth_map.min()
        depth_max = depth_map.max()
        if depth_max > depth_min:
            normalized = (depth_map - depth_min) / (depth_max - depth_min)
            return normalized * 100.0
        return depth_map
    def get_estimator_params(self) -> Dict:
        return {'type': 'LearningBased', 'model_type': self.model_type, 'model_path': self.model_path}
class DepthFromDefocus(MonocularDepthEstimator):
    def __init__(self, camera_matrix: np.ndarray, aperture_size: float = 2.8, focal_distance: float = 1.0):
        super().__init__(camera_matrix)
        self.aperture_size = aperture_size
        self.focal_distance = focal_distance
    def estimate_depth(self, image: np.ndarray, **kwargs) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        blur_map = self._compute_blur_map(gray)
        depth_map = self._blur_to_depth(blur_map)
        return depth_map
    def _compute_blur_map(self, image: np.ndarray) -> np.ndarray:
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        blur_map = np.abs(laplacian)
        blur_map = cv2.GaussianBlur(blur_map, (5, 5), 0)
        return blur_map
    def _blur_to_depth(self, blur_map: np.ndarray) -> np.ndarray:
        blur_normalized = blur_map / (blur_map.max() + 1e-8)
        sharpness = 1.0 - blur_normalized
        depth_map = self.focal_distance / (sharpness + 1e-8)
        depth_map = np.clip(depth_map, 0.1, 100.0)
        return depth_map
    def get_estimator_params(self) -> Dict:
        return {'type': 'DepthFromDefocus', 'aperture_size': self.aperture_size, 'focal_distance': self.focal_distance}
class DepthFromShadows(MonocularDepthEstimator):
    def __init__(self, camera_matrix: np.ndarray, light_direction: np.ndarray = np.array([0, -1, 1])):
        super().__init__(camera_matrix)
        self.light_direction = light_direction / np.linalg.norm(light_direction)
    def estimate_depth(self, image: np.ndarray, **kwargs) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        shadow_map = self._detect_shadows(gray)
        depth_map = self._shadows_to_depth(shadow_map, gray)
        return depth_map
    def _detect_shadows(self, image: np.ndarray) -> np.ndarray:
        mean_intensity = np.mean(image)
        shadow_threshold = mean_intensity * 0.7
        shadow_map = (image < shadow_threshold).astype(np.float32)
        shadow_map = cv2.morphologyEx(shadow_map, cv2.MORPH_CLOSE, np.ones((5, 5)))
        return shadow_map
    def _shadows_to_depth(self, shadow_map: np.ndarray, image: np.ndarray) -> np.ndarray:
        gradient_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        gradient_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
        depth_estimate = gradient_magnitude * (1 + shadow_map)
        depth_estimate = cv2.GaussianBlur(depth_estimate, (7, 7), 0)
        depth_normalized = (depth_estimate - depth_estimate.min()) / (depth_estimate.max() - depth_estimate.min() + 1e-8)
        depth_map = depth_normalized * 50.0 + 1.0
        return depth_map
    def get_estimator_params(self) -> Dict:
        return {'type': 'DepthFromShadows', 'light_direction': self.light_direction.tolist()}
class MonocularDepthEvaluator:
    @staticmethod
    def evaluate_against_lidar(estimated_depth: np.ndarray, lidar_depth: np.ndarray, camera_matrix: np.ndarray, lidar_to_camera_transform: np.ndarray) -> Dict:
        projected_lidar = MonocularDepthEvaluator._project_lidar_to_image(lidar_depth, camera_matrix, lidar_to_camera_transform)
        valid_mask = (estimated_depth > 0) & (projected_lidar > 0)
        if np.sum(valid_mask) == 0:
            return {'rmse': float('inf'), 'mae': float('inf'), 'abs_rel': float('inf'), 'valid_pixels': 0}
        est_valid = estimated_depth[valid_mask]
        lidar_valid = projected_lidar[valid_mask]
        rmse = np.sqrt(np.mean((est_valid - lidar_valid) ** 2))
        mae = np.mean(np.abs(est_valid - lidar_valid))
        abs_rel = np.mean(np.abs(est_valid - lidar_valid) / lidar_valid)
        return {'rmse': rmse, 'mae': mae, 'abs_rel': abs_rel, 'valid_pixels': np.sum(valid_mask), 'correlation': np.corrcoef(est_valid, lidar_valid)[0, 1]}
    @staticmethod
    def _project_lidar_to_image(lidar_points: np.ndarray, camera_matrix: np.ndarray, transform: np.ndarray) -> np.ndarray:
        if len(lidar_points.shape) == 1:
            height, width = 376, 1241
            depth_image = np.zeros((height, width))
            return depth_image
        points_camera = (transform @ np.hstack([lidar_points[:, :3], np.ones((len(lidar_points), 1))]).T).T
        points_camera = points_camera[:, :3]
        valid_mask = points_camera[:, 2] > 0
        points_valid = points_camera[valid_mask]
        if len(points_valid) == 0:
            return np.zeros((376, 1241))
        projected = camera_matrix @ points_valid.T
        projected = projected[:2] / projected[2]
        u, v = projected[0], projected[1]
        height, width = 376, 1241
        depth_image = np.zeros((height, width))
        valid_pixels = (u >= 0) & (u < width) & (v >= 0) & (v < height)
        u_valid = u[valid_pixels].astype(int)
        v_valid = v[valid_pixels].astype(int)
        depths_valid = points_valid[valid_pixels, 2]
        depth_image[v_valid, u_valid] = depths_valid
        return depth_image
    @staticmethod
    def compute_scale_invariant_metrics(estimated_depth: np.ndarray, ground_truth_depth: np.ndarray) -> Dict:
        valid_mask = (estimated_depth > 0) & (ground_truth_depth > 0)
        if np.sum(valid_mask) == 0:
            return {'si_rmse': float('inf'), 'si_mae': float('inf'), 'scale_factor': 1.0}
        est_valid = estimated_depth[valid_mask]
        gt_valid = ground_truth_depth[valid_mask]
        scale_factor = np.median(gt_valid / est_valid)
        est_scaled = est_valid * scale_factor
        si_rmse = np.sqrt(np.mean((est_scaled - gt_valid) ** 2))
        si_mae = np.mean(np.abs(est_scaled - gt_valid))
        return {'si_rmse': si_rmse, 'si_mae': si_mae, 'scale_factor': scale_factor, 'valid_pixels': np.sum(valid_mask)}
class DepthFusion:
    @staticmethod
    def fuse_multiple_estimates(depth_estimates: List[np.ndarray], weights: Optional[List[float]] = None, method: str = 'weighted_average') -> np.ndarray:
        if not depth_estimates:
            return np.array([])
        if weights is None:
            weights = [1.0] * len(depth_estimates)
        weights = np.array(weights)
        weights = weights / np.sum(weights)
        if method == 'weighted_average':
            fused_depth = np.zeros_like(depth_estimates[0])
            total_weight = np.zeros_like(depth_estimates[0])
            for depth, weight in zip(depth_estimates, weights):
                valid_mask = depth > 0
                fused_depth[valid_mask] += depth[valid_mask] * weight
                total_weight[valid_mask] += weight
            valid_fusion_mask = total_weight > 0
            fused_depth[valid_fusion_mask] /= total_weight[valid_fusion_mask]
            return fused_depth
        elif method == 'median':
            depth_stack = np.stack(depth_estimates, axis=-1)
            valid_mask = depth_stack > 0
            fused_depth = np.zeros(depth_estimates[0].shape)
            for i in range(depth_stack.shape[0]):
                for j in range(depth_stack.shape[1]):
                    valid_depths = depth_stack[i, j, valid_mask[i, j]]
                    if len(valid_depths) > 0:
                        fused_depth[i, j] = np.median(valid_depths)
            return fused_depth
        else:
            return depth_estimates[0]
    @staticmethod
    def confidence_weighted_fusion(depth_estimates: List[np.ndarray], confidence_maps: List[np.ndarray]) -> np.ndarray:
        if len(depth_estimates) != len(confidence_maps):
            raise ValueError("Number of depth estimates must match number of confidence maps")
        fused_depth = np.zeros_like(depth_estimates[0])
        total_confidence = np.zeros_like(depth_estimates[0])
        for depth, confidence in zip(depth_estimates, confidence_maps):
            valid_mask = (depth > 0) & (confidence > 0)
            fused_depth[valid_mask] += depth[valid_mask] * confidence[valid_mask]
            total_confidence[valid_mask] += confidence[valid_mask]
        valid_fusion_mask = total_confidence > 0
        fused_depth[valid_fusion_mask] /= total_confidence[valid_fusion_mask]
        return fused_depth