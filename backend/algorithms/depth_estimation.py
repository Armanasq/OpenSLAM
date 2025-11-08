import sys
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from abc import ABC, abstractmethod
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
class StereoMatcher(ABC):
    def __init__(self, min_disparity: int = 0, num_disparities: int = 64, block_size: int = 15):
        self.min_disparity = min_disparity
        self.num_disparities = num_disparities
        self.block_size = block_size
        self.matcher = None
    @abstractmethod
    def compute_disparity(self, left_image: np.ndarray, right_image: np.ndarray) -> np.ndarray:
        pass
    @abstractmethod
    def get_matcher_params(self) -> Dict:
        pass
class StereoBMMatcher(StereoMatcher):
    def __init__(self, min_disparity: int = 0, num_disparities: int = 64, block_size: int = 15, p1: int = 0, p2: int = 0, disp12_max_diff: int = -1, pre_filter_cap: int = 31, uniqueness_ratio: int = 15, speckle_window_size: int = 0, speckle_range: int = 0):
        super().__init__(min_disparity, num_disparities, block_size)
        self.p1 = p1
        self.p2 = p2
        self.disp12_max_diff = disp12_max_diff
        self.pre_filter_cap = pre_filter_cap
        self.uniqueness_ratio = uniqueness_ratio
        self.speckle_window_size = speckle_window_size
        self.speckle_range = speckle_range
        self.matcher = cv2.StereoBM_create(numDisparities=num_disparities, blockSize=block_size)
        self.matcher.setMinDisparity(min_disparity)
        self.matcher.setPreFilterCap(pre_filter_cap)
        self.matcher.setUniquenessRatio(uniqueness_ratio)
        self.matcher.setSpeckleWindowSize(speckle_window_size)
        self.matcher.setSpeckleRange(speckle_range)
        if disp12_max_diff >= 0:
            self.matcher.setDisp12MaxDiff(disp12_max_diff)
    def compute_disparity(self, left_image: np.ndarray, right_image: np.ndarray) -> np.ndarray:
        if len(left_image.shape) == 3:
            left_image = cv2.cvtColor(left_image, cv2.COLOR_BGR2GRAY)
        if len(right_image.shape) == 3:
            right_image = cv2.cvtColor(right_image, cv2.COLOR_BGR2GRAY)
        disparity = self.matcher.compute(left_image, right_image)
        return disparity.astype(np.float32) / 16.0
    def get_matcher_params(self) -> Dict:
        return {'type': 'StereoBM', 'min_disparity': self.min_disparity, 'num_disparities': self.num_disparities, 'block_size': self.block_size, 'pre_filter_cap': self.pre_filter_cap, 'uniqueness_ratio': self.uniqueness_ratio, 'speckle_window_size': self.speckle_window_size, 'speckle_range': self.speckle_range}
class StereoSGBMMatcher(StereoMatcher):
    def __init__(self, min_disparity: int = 0, num_disparities: int = 64, block_size: int = 3, p1: int = 0, p2: int = 0, disp12_max_diff: int = -1, pre_filter_cap: int = 0, uniqueness_ratio: int = 10, speckle_window_size: int = 100, speckle_range: int = 32, mode: int = cv2.STEREO_SGBM_MODE_SGBM):
        super().__init__(min_disparity, num_disparities, block_size)
        self.p1 = p1 if p1 > 0 else 8 * 3 * block_size * block_size
        self.p2 = p2 if p2 > 0 else 32 * 3 * block_size * block_size
        self.disp12_max_diff = disp12_max_diff
        self.pre_filter_cap = pre_filter_cap
        self.uniqueness_ratio = uniqueness_ratio
        self.speckle_window_size = speckle_window_size
        self.speckle_range = speckle_range
        self.mode = mode
        self.matcher = cv2.StereoSGBM_create(minDisparity=min_disparity, numDisparities=num_disparities, blockSize=block_size, P1=self.p1, P2=self.p2, disp12MaxDiff=disp12_max_diff, preFilterCap=pre_filter_cap, uniquenessRatio=uniqueness_ratio, speckleWindowSize=speckle_window_size, speckleRange=speckle_range, mode=mode)
    def compute_disparity(self, left_image: np.ndarray, right_image: np.ndarray) -> np.ndarray:
        disparity = self.matcher.compute(left_image, right_image)
        return disparity.astype(np.float32) / 16.0
    def get_matcher_params(self) -> Dict:
        return {'type': 'StereoSGBM', 'min_disparity': self.min_disparity, 'num_disparities': self.num_disparities, 'block_size': self.block_size, 'p1': self.p1, 'p2': self.p2, 'disp12_max_diff': self.disp12_max_diff, 'pre_filter_cap': self.pre_filter_cap, 'uniqueness_ratio': self.uniqueness_ratio, 'speckle_window_size': self.speckle_window_size, 'speckle_range': self.speckle_range, 'mode': self.mode}
class DepthMapProcessor:
    def __init__(self, camera_matrix: np.ndarray, baseline: float):
        self.camera_matrix = camera_matrix
        self.baseline = baseline
        self.focal_length = camera_matrix[0, 0]
        self.cx = camera_matrix[0, 2]
        self.cy = camera_matrix[1, 2]
    def disparity_to_depth(self, disparity: np.ndarray, min_depth: float = 0.1, max_depth: float = 100.0) -> np.ndarray:
        valid_mask = disparity > 0
        depth = np.zeros_like(disparity)
        depth[valid_mask] = (self.baseline * self.focal_length) / disparity[valid_mask]
        depth = np.clip(depth, min_depth, max_depth)
        depth[~valid_mask] = 0
        return depth
    def depth_to_pointcloud(self, depth: np.ndarray, color_image: Optional[np.ndarray] = None) -> np.ndarray:
        height, width = depth.shape
        u, v = np.meshgrid(np.arange(width), np.arange(height))
        valid_mask = depth > 0
        u_valid = u[valid_mask]
        v_valid = v[valid_mask]
        depth_valid = depth[valid_mask]
        x = (u_valid - self.cx) * depth_valid / self.focal_length
        y = (v_valid - self.cy) * depth_valid / self.focal_length
        z = depth_valid
        points = np.column_stack([x, y, z])
        if color_image is not None:
            if len(color_image.shape) == 3:
                colors = color_image[valid_mask] / 255.0
                points = np.column_stack([points, colors])
            else:
                gray_colors = color_image[valid_mask] / 255.0
                points = np.column_stack([points, gray_colors, gray_colors, gray_colors])
        return points
    def filter_depth_map(self, depth: np.ndarray, method: str = 'median', kernel_size: int = 5, sigma: float = 1.0) -> np.ndarray:
        if method == 'median':
            return cv2.medianBlur(depth.astype(np.float32), kernel_size)
        elif method == 'gaussian':
            return cv2.GaussianBlur(depth, (kernel_size, kernel_size), sigma)
        elif method == 'bilateral':
            return cv2.bilateralFilter(depth.astype(np.float32), kernel_size, sigma * 2, sigma)
        elif method == 'morphological':
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            opened = cv2.morphologyEx(depth, cv2.MORPH_OPEN, kernel)
            return cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
        else:
            return depth
    def fill_depth_holes(self, depth: np.ndarray, method: str = 'inpaint', max_hole_size: int = 10) -> np.ndarray:
        if method == 'inpaint':
            mask = (depth == 0).astype(np.uint8)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max_hole_size, max_hole_size))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            filled = cv2.inpaint(depth.astype(np.float32), mask, max_hole_size, cv2.INPAINT_TELEA)
            return filled
        elif method == 'interpolation':
            from scipy import interpolate
            valid_mask = depth > 0
            if np.sum(valid_mask) < 4:
                return depth
            height, width = depth.shape
            y, x = np.mgrid[0:height, 0:width]
            valid_points = np.column_stack([x[valid_mask], y[valid_mask]])
            valid_values = depth[valid_mask]
            try:
                interp = interpolate.griddata(valid_points, valid_values, (x, y), method='linear', fill_value=0)
                return interp
            except:
                return depth
        else:
            return depth
    def compute_depth_statistics(self, depth: np.ndarray) -> Dict:
        valid_mask = depth > 0
        if np.sum(valid_mask) == 0:
            return {'valid_pixels': 0, 'coverage': 0.0, 'mean_depth': 0.0, 'std_depth': 0.0, 'min_depth': 0.0, 'max_depth': 0.0}
        valid_depths = depth[valid_mask]
        return {'valid_pixels': len(valid_depths), 'coverage': len(valid_depths) / depth.size, 'mean_depth': np.mean(valid_depths), 'std_depth': np.std(valid_depths), 'min_depth': np.min(valid_depths), 'max_depth': np.max(valid_depths), 'median_depth': np.median(valid_depths)}
class DepthVisualization:
    @staticmethod
    def colorize_depth(depth: np.ndarray, min_depth: Optional[float] = None, max_depth: Optional[float] = None, colormap: int = cv2.COLORMAP_JET) -> np.ndarray:
        valid_mask = depth > 0
        if np.sum(valid_mask) == 0:
            return np.zeros((*depth.shape, 3), dtype=np.uint8)
        if min_depth is None:
            min_depth = np.min(depth[valid_mask])
        if max_depth is None:
            max_depth = np.max(depth[valid_mask])
        normalized_depth = np.zeros_like(depth)
        normalized_depth[valid_mask] = (depth[valid_mask] - min_depth) / (max_depth - min_depth)
        normalized_depth = np.clip(normalized_depth * 255, 0, 255).astype(np.uint8)
        colored_depth = cv2.applyColorMap(normalized_depth, colormap)
        colored_depth[~valid_mask] = [0, 0, 0]
        return colored_depth
    @staticmethod
    def create_depth_histogram(depth: np.ndarray, bins: int = 50) -> Tuple[np.ndarray, np.ndarray]:
        valid_depths = depth[depth > 0]
        if len(valid_depths) == 0:
            return np.array([]), np.array([])
        hist, bin_edges = np.histogram(valid_depths, bins=bins)
        return hist, bin_edges
    @staticmethod
    def overlay_depth_on_image(image: np.ndarray, depth: np.ndarray, alpha: float = 0.6) -> np.ndarray:
        colored_depth = DepthVisualization.colorize_depth(depth)
        if len(image.shape) == 2:
            image_color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            image_color = image.copy()
        valid_mask = depth > 0
        overlay = image_color.copy()
        overlay[valid_mask] = cv2.addWeighted(image_color[valid_mask], 1 - alpha, colored_depth[valid_mask], alpha, 0)
        return overlay
class StereoCalibration:
    def __init__(self):
        self.camera_matrix_left = None
        self.camera_matrix_right = None
        self.dist_coeffs_left = None
        self.dist_coeffs_right = None
        self.R = None
        self.T = None
        self.E = None
        self.F = None
        self.baseline = None
    def calibrate_stereo_camera(self, object_points: List[np.ndarray], image_points_left: List[np.ndarray], image_points_right: List[np.ndarray], image_size: Tuple[int, int]) -> Dict:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        flags = cv2.CALIB_FIX_INTRINSIC
        ret, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(object_points, image_points_left, image_points_right, None, None, None, None, image_size, criteria=criteria, flags=flags)
        self.camera_matrix_left = K1
        self.camera_matrix_right = K2
        self.dist_coeffs_left = D1
        self.dist_coeffs_right = D2
        self.R = R
        self.T = T
        self.E = E
        self.F = F
        self.baseline = np.linalg.norm(T)
        return {'success': ret, 'reprojection_error': ret, 'baseline': self.baseline, 'rotation_angle': np.degrees(np.arccos((np.trace(R) - 1) / 2))}
    def rectify_stereo_images(self, left_image: np.ndarray, right_image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.camera_matrix_left is None:
            raise ValueError("Stereo camera not calibrated")
        image_size = (left_image.shape[1], left_image.shape[0])
        R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(self.camera_matrix_left, self.dist_coeffs_left, self.camera_matrix_right, self.dist_coeffs_right, image_size, self.R, self.T)
        map1_left, map2_left = cv2.initUndistortRectifyMap(self.camera_matrix_left, self.dist_coeffs_left, R1, P1, image_size, cv2.CV_16SC2)
        map1_right, map2_right = cv2.initUndistortRectifyMap(self.camera_matrix_right, self.dist_coeffs_right, R2, P2, image_size, cv2.CV_16SC2)
        rectified_left = cv2.remap(left_image, map1_left, map2_left, cv2.INTER_LINEAR)
        rectified_right = cv2.remap(right_image, map1_right, map2_right, cv2.INTER_LINEAR)
        return rectified_left, rectified_right, Q
class DepthEvaluator:
    @staticmethod
    def evaluate_depth_accuracy(estimated_depth: np.ndarray, ground_truth_depth: np.ndarray, max_depth: float = 80.0) -> Dict:
        valid_mask = (estimated_depth > 0) & (ground_truth_depth > 0) & (ground_truth_depth < max_depth)
        if np.sum(valid_mask) == 0:
            return {'rmse': float('inf'), 'mae': float('inf'), 'abs_rel': float('inf'), 'sq_rel': float('inf'), 'accuracy_1_25': 0.0, 'accuracy_1_25_2': 0.0, 'accuracy_1_25_3': 0.0}
        est_valid = estimated_depth[valid_mask]
        gt_valid = ground_truth_depth[valid_mask]
        rmse = np.sqrt(np.mean((est_valid - gt_valid) ** 2))
        mae = np.mean(np.abs(est_valid - gt_valid))
        abs_rel = np.mean(np.abs(est_valid - gt_valid) / gt_valid)
        sq_rel = np.mean(((est_valid - gt_valid) ** 2) / gt_valid)
        ratio = np.maximum(est_valid / gt_valid, gt_valid / est_valid)
        accuracy_1_25 = np.mean(ratio < 1.25)
        accuracy_1_25_2 = np.mean(ratio < 1.25 ** 2)
        accuracy_1_25_3 = np.mean(ratio < 1.25 ** 3)
        return {'rmse': rmse, 'mae': mae, 'abs_rel': abs_rel, 'sq_rel': sq_rel, 'accuracy_1_25': accuracy_1_25, 'accuracy_1_25_2': accuracy_1_25_2, 'accuracy_1_25_3': accuracy_1_25_3, 'valid_pixels': np.sum(valid_mask)}
    @staticmethod
    def compute_depth_completion_metrics(sparse_depth: np.ndarray, dense_depth: np.ndarray, ground_truth: np.ndarray) -> Dict:
        sparse_metrics = DepthEvaluator.evaluate_depth_accuracy(sparse_depth, ground_truth)
        dense_metrics = DepthEvaluator.evaluate_depth_accuracy(dense_depth, ground_truth)
        improvement = {}
        for key in ['rmse', 'mae', 'abs_rel']:
            if sparse_metrics[key] != 0:
                improvement[f'{key}_improvement'] = (sparse_metrics[key] - dense_metrics[key]) / sparse_metrics[key]
            else:
                improvement[f'{key}_improvement'] = 0.0
        return {'sparse_metrics': sparse_metrics, 'dense_metrics': dense_metrics, 'improvement': improvement}