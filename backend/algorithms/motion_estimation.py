import sys
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from abc import ABC, abstractmethod
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
class MotionEstimator(ABC):
    def __init__(self, camera_matrix: np.ndarray):
        self.camera_matrix = camera_matrix
        self.distortion_coeffs = np.zeros((4, 1))
    @abstractmethod
    def estimate_motion(self, pts1: np.ndarray, pts2: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        pass
    @abstractmethod
    def get_estimator_params(self) -> Dict:
        pass
class EssentialMatrixEstimator(MotionEstimator):
    def __init__(self, camera_matrix: np.ndarray, method: int = cv2.RANSAC, prob: float = 0.999, threshold: float = 1.0, max_iters: int = 1000):
        super().__init__(camera_matrix)
        self.method = method
        self.prob = prob
        self.threshold = threshold
        self.max_iters = max_iters
    def estimate_motion(self, pts1: np.ndarray, pts2: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if len(pts1) < 5 or len(pts2) < 5:
            return np.eye(3), np.zeros((3, 1)), np.ones(len(pts1), dtype=bool)
        E, mask = cv2.findEssentialMat(pts1, pts2, self.camera_matrix, method=self.method, prob=self.prob, threshold=self.threshold, maxIters=self.max_iters)
        if E is None:
            return np.eye(3), np.zeros((3, 1)), np.ones(len(pts1), dtype=bool)
        retval, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, self.camera_matrix, mask=mask)
        return R, t, mask.ravel().astype(bool)
    def get_estimator_params(self) -> Dict:
        return {'type': 'EssentialMatrix', 'method': self.method, 'prob': self.prob, 'threshold': self.threshold, 'max_iters': self.max_iters}
class FundamentalMatrixEstimator(MotionEstimator):
    def __init__(self, camera_matrix: np.ndarray, method: int = cv2.FM_RANSAC, ransac_threshold: float = 1.0, confidence: float = 0.99):
        super().__init__(camera_matrix)
        self.method = method
        self.ransac_threshold = ransac_threshold
        self.confidence = confidence
    def estimate_motion(self, pts1: np.ndarray, pts2: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if len(pts1) < 8 or len(pts2) < 8:
            return np.eye(3), np.zeros((3, 1)), np.ones(len(pts1), dtype=bool)
        F, mask = cv2.findFundamentalMat(pts1, pts2, method=self.method, ransacReprojThreshold=self.ransac_threshold, confidence=self.confidence)
        if F is None:
            return np.eye(3), np.zeros((3, 1)), np.ones(len(pts1), dtype=bool)
        E = self.camera_matrix.T @ F @ self.camera_matrix
        retval, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, self.camera_matrix)
        return R, t, mask.ravel().astype(bool)
    def get_estimator_params(self) -> Dict:
        return {'type': 'FundamentalMatrix', 'method': self.method, 'ransac_threshold': self.ransac_threshold, 'confidence': self.confidence}
class HomographyEstimator(MotionEstimator):
    def __init__(self, camera_matrix: np.ndarray, method: int = cv2.RANSAC, ransac_threshold: float = 3.0, confidence: float = 0.99, max_iters: int = 2000):
        super().__init__(camera_matrix)
        self.method = method
        self.ransac_threshold = ransac_threshold
        self.confidence = confidence
        self.max_iters = max_iters
    def estimate_motion(self, pts1: np.ndarray, pts2: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if len(pts1) < 4 or len(pts2) < 4:
            return np.eye(3), np.zeros((3, 1)), np.ones(len(pts1), dtype=bool)
        H, mask = cv2.findHomography(pts1, pts2, method=self.method, ransacReprojThreshold=self.ransac_threshold, confidence=self.confidence, maxIters=self.max_iters)
        if H is None:
            return np.eye(3), np.zeros((3, 1)), np.ones(len(pts1), dtype=bool)
        num_solutions, Rs, ts, normals = cv2.decomposeHomographyMat(H, self.camera_matrix)
        if num_solutions == 0:
            return np.eye(3), np.zeros((3, 1)), mask.ravel().astype(bool)
        R, t = Rs[0], ts[0]
        return R, t, mask.ravel().astype(bool)
    def get_estimator_params(self) -> Dict:
        return {'type': 'Homography', 'method': self.method, 'ransac_threshold': self.ransac_threshold, 'confidence': self.confidence, 'max_iters': self.max_iters}
class PnPEstimator(MotionEstimator):
    def __init__(self, camera_matrix: np.ndarray, method: int = cv2.SOLVEPNP_ITERATIVE, use_extrinsic_guess: bool = False, ransac_threshold: float = 8.0, confidence: float = 0.99, max_iters: int = 100):
        super().__init__(camera_matrix)
        self.method = method
        self.use_extrinsic_guess = use_extrinsic_guess
        self.ransac_threshold = ransac_threshold
        self.confidence = confidence
        self.max_iters = max_iters
    def estimate_motion_3d2d(self, object_points: np.ndarray, image_points: np.ndarray, initial_rvec: Optional[np.ndarray] = None, initial_tvec: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if len(object_points) < 4 or len(image_points) < 4:
            return np.eye(3), np.zeros((3, 1)), np.ones(len(object_points), dtype=bool)
        if self.method == cv2.SOLVEPNP_RANSAC:
            success, rvec, tvec, inliers = cv2.solvePnPRansac(object_points, image_points, self.camera_matrix, self.distortion_coeffs, reprojectionError=self.ransac_threshold, confidence=self.confidence, iterationsCount=self.max_iters)
            mask = np.zeros(len(object_points), dtype=bool)
            if inliers is not None:
                mask[inliers.ravel()] = True
        else:
            success, rvec, tvec = cv2.solvePnP(object_points, image_points, self.camera_matrix, self.distortion_coeffs, rvec=initial_rvec, tvec=initial_tvec, useExtrinsicGuess=self.use_extrinsic_guess, flags=self.method)
            mask = np.ones(len(object_points), dtype=bool)
        if not success:
            return np.eye(3), np.zeros((3, 1)), np.ones(len(object_points), dtype=bool)
        R, _ = cv2.Rodrigues(rvec)
        return R, tvec, mask
    def estimate_motion(self, pts1: np.ndarray, pts2: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        raise NotImplementedError("PnP requires 3D points. Use estimate_motion_3d2d instead.")
    def get_estimator_params(self) -> Dict:
        return {'type': 'PnP', 'method': self.method, 'use_extrinsic_guess': self.use_extrinsic_guess, 'ransac_threshold': self.ransac_threshold, 'confidence': self.confidence, 'max_iters': self.max_iters}
class Triangulation:
    def __init__(self, camera_matrix: np.ndarray):
        self.camera_matrix = camera_matrix
    def triangulate_points(self, pts1: np.ndarray, pts2: np.ndarray, R1: np.ndarray, t1: np.ndarray, R2: np.ndarray, t2: np.ndarray) -> np.ndarray:
        P1 = self.camera_matrix @ np.hstack([R1, t1.reshape(-1, 1)])
        P2 = self.camera_matrix @ np.hstack([R2, t2.reshape(-1, 1)])
        pts1_norm = pts1.T
        pts2_norm = pts2.T
        points_4d = cv2.triangulatePoints(P1, P2, pts1_norm, pts2_norm)
        points_3d = points_4d[:3] / points_4d[3]
        return points_3d.T
    def triangulate_stereo(self, pts_left: np.ndarray, pts_right: np.ndarray, baseline: float, focal_length: float) -> np.ndarray:
        disparity = pts_left[:, 0] - pts_right[:, 0]
        disparity[disparity == 0] = 1e-6
        depth = (baseline * focal_length) / disparity
        cx, cy = self.camera_matrix[0, 2], self.camera_matrix[1, 2]
        fx, fy = self.camera_matrix[0, 0], self.camera_matrix[1, 1]
        x = (pts_left[:, 0] - cx) * depth / fx
        y = (pts_left[:, 1] - cy) * depth / fy
        points_3d = np.column_stack([x, y, depth])
        return points_3d
    def check_triangulation_quality(self, points_3d: np.ndarray, R: np.ndarray, t: np.ndarray, pts1: np.ndarray, pts2: np.ndarray) -> Dict:
        if len(points_3d) == 0:
            return {'valid_points': 0, 'reprojection_error': float('inf'), 'depth_positive_ratio': 0.0}
        points_cam1 = points_3d
        points_cam2 = (R @ points_3d.T + t.reshape(-1, 1)).T
        valid_mask = (points_cam1[:, 2] > 0) & (points_cam2[:, 2] > 0)
        valid_points = np.sum(valid_mask)
        if valid_points == 0:
            return {'valid_points': 0, 'reprojection_error': float('inf'), 'depth_positive_ratio': 0.0}
        proj1 = self.camera_matrix @ points_cam1[valid_mask].T
        proj1 = (proj1[:2] / proj1[2]).T
        proj2 = self.camera_matrix @ points_cam2[valid_mask].T
        proj2 = (proj2[:2] / proj2[2]).T
        error1 = np.linalg.norm(proj1 - pts1[valid_mask], axis=1)
        error2 = np.linalg.norm(proj2 - pts2[valid_mask], axis=1)
        reprojection_error = np.mean(error1 + error2)
        return {'valid_points': valid_points, 'reprojection_error': reprojection_error, 'depth_positive_ratio': valid_points / len(points_3d), 'mean_depth': np.mean(points_3d[valid_mask, 2]), 'depth_std': np.std(points_3d[valid_mask, 2])}
class PoseRecovery:
    def __init__(self, camera_matrix: np.ndarray):
        self.camera_matrix = camera_matrix
    def recover_pose_from_essential(self, E: np.ndarray, pts1: np.ndarray, pts2: np.ndarray) -> Tuple[np.ndarray, np.ndarray, int]:
        retval, R, t, mask = cv2.recoverPose(E, pts1, pts2, self.camera_matrix)
        return R, t, retval
    def decompose_essential_matrix(self, E: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
        U, S, Vt = np.linalg.svd(E)
        if np.linalg.det(U) < 0:
            U *= -1
        if np.linalg.det(Vt) < 0:
            Vt *= -1
        W = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        R1 = U @ W @ Vt
        R2 = U @ W.T @ Vt
        t = U[:, 2]
        return [(R1, t), (R1, -t), (R2, t), (R2, -t)]
    def select_best_pose(self, pose_candidates: List[Tuple[np.ndarray, np.ndarray]], pts1: np.ndarray, pts2: np.ndarray) -> Tuple[np.ndarray, np.ndarray, int]:
        best_pose = None
        max_infront = 0
        triangulator = Triangulation(self.camera_matrix)
        for R, t in pose_candidates:
            try:
                points_3d = triangulator.triangulate_points(pts1, pts2, np.eye(3), np.zeros(3), R, t)
                points_cam1 = points_3d
                points_cam2 = (R @ points_3d.T + t.reshape(-1, 1)).T
                infront_cam1 = np.sum(points_cam1[:, 2] > 0)
                infront_cam2 = np.sum(points_cam2[:, 2] > 0)
                total_infront = min(infront_cam1, infront_cam2)
                if total_infront > max_infront:
                    max_infront = total_infront
                    best_pose = (R, t)
            except:
                continue
        if best_pose is None:
            return np.eye(3), np.zeros((3, 1)), 0
        return best_pose[0], best_pose[1].reshape(-1, 1), max_infront
class MotionValidation:
    @staticmethod
    def validate_rotation_matrix(R: np.ndarray, tolerance: float = 1e-6) -> bool:
        if R.shape != (3, 3):
            return False
        det_R = np.linalg.det(R)
        if abs(det_R - 1.0) > tolerance:
            return False
        should_be_identity = R @ R.T
        identity = np.eye(3)
        if np.max(np.abs(should_be_identity - identity)) > tolerance:
            return False
        return True
    @staticmethod
    def validate_translation_vector(t: np.ndarray) -> bool:
        if t.shape not in [(3,), (3, 1)]:
            return False
        if np.any(np.isnan(t)) or np.any(np.isinf(t)):
            return False
        return True
    @staticmethod
    def compute_motion_magnitude(R: np.ndarray, t: np.ndarray) -> Dict:
        rotation_angle = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
        translation_magnitude = np.linalg.norm(t)
        return {'rotation_angle_rad': rotation_angle, 'rotation_angle_deg': np.degrees(rotation_angle), 'translation_magnitude': translation_magnitude}
    @staticmethod
    def check_motion_consistency(R_prev: np.ndarray, t_prev: np.ndarray, R_curr: np.ndarray, t_curr: np.ndarray, max_rotation_change: float = np.pi/6, max_translation_change: float = 2.0) -> bool:
        R_rel = R_curr @ R_prev.T
        rotation_change = np.arccos(np.clip((np.trace(R_rel) - 1) / 2, -1, 1))
        if rotation_change > max_rotation_change:
            return False
        t_change = np.linalg.norm(t_curr - t_prev)
        if t_change > max_translation_change:
            return False
        return True