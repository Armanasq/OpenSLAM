import sys
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from abc import ABC, abstractmethod
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
class FeatureDetector(ABC):
    def __init__(self, max_features: int = 1000):
        self.max_features = max_features
        self.detector = None
    @abstractmethod
    def detect_and_compute(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[List, np.ndarray]:
        pass
    @abstractmethod
    def get_detector_params(self) -> Dict:
        pass
class ORBDetector(FeatureDetector):
    def __init__(self, max_features: int = 1000, scale_factor: float = 1.2, n_levels: int = 8, edge_threshold: int = 31, first_level: int = 0, wta_k: int = 2, score_type: int = cv2.ORB_HARRIS_SCORE, patch_size: int = 31, fast_threshold: int = 20):
        super().__init__(max_features)
        self.scale_factor = scale_factor
        self.n_levels = n_levels
        self.edge_threshold = edge_threshold
        self.first_level = first_level
        self.wta_k = wta_k
        self.score_type = score_type
        self.patch_size = patch_size
        self.fast_threshold = fast_threshold
        self.detector = cv2.ORB_create(nfeatures=max_features, scaleFactor=scale_factor, nlevels=n_levels, edgeThreshold=edge_threshold, firstLevel=first_level, WTA_K=wta_k, scoreType=score_type, patchSize=patch_size, fastThreshold=fast_threshold)
    def detect_and_compute(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[List, np.ndarray]:
        keypoints, descriptors = self.detector.detectAndCompute(image, mask)
        return keypoints, descriptors
    def get_detector_params(self) -> Dict:
        return {'type': 'ORB', 'max_features': self.max_features, 'scale_factor': self.scale_factor, 'n_levels': self.n_levels, 'edge_threshold': self.edge_threshold, 'patch_size': self.patch_size, 'fast_threshold': self.fast_threshold}
class SIFTDetector(FeatureDetector):
    def __init__(self, max_features: int = 1000, n_octave_layers: int = 3, contrast_threshold: float = 0.04, edge_threshold: float = 10.0, sigma: float = 1.6):
        super().__init__(max_features)
        self.n_octave_layers = n_octave_layers
        self.contrast_threshold = contrast_threshold
        self.edge_threshold = edge_threshold
        self.sigma = sigma
        self.detector = cv2.SIFT_create(nfeatures=max_features, nOctaveLayers=n_octave_layers, contrastThreshold=contrast_threshold, edgeThreshold=edge_threshold, sigma=sigma)
    def detect_and_compute(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[List, np.ndarray]:
        keypoints, descriptors = self.detector.detectAndCompute(image, mask)
        return keypoints, descriptors
    def get_detector_params(self) -> Dict:
        return {'type': 'SIFT', 'max_features': self.max_features, 'n_octave_layers': self.n_octave_layers, 'contrast_threshold': self.contrast_threshold, 'edge_threshold': self.edge_threshold, 'sigma': self.sigma}
class SURFDetector(FeatureDetector):
    def __init__(self, max_features: int = 1000, hessian_threshold: float = 400.0, n_octaves: int = 4, n_octave_layers: int = 3, extended: bool = False, upright: bool = False):
        super().__init__(max_features)
        self.hessian_threshold = hessian_threshold
        self.n_octaves = n_octaves
        self.n_octave_layers = n_octave_layers
        self.extended = extended
        self.upright = upright
        try:
            self.detector = cv2.xfeatures2d.SURF_create(hessianThreshold=hessian_threshold, nOctaves=n_octaves, nOctaveLayers=n_octave_layers, extended=extended, upright=upright)
        except AttributeError:
            self.detector = None
    def detect_and_compute(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> Tuple[List, np.ndarray]:
        if self.detector is None:
            raise RuntimeError("SURF detector not available. Install opencv-contrib-python.")
        keypoints, descriptors = self.detector.detectAndCompute(image, mask)
        if len(keypoints) > self.max_features:
            keypoints = sorted(keypoints, key=lambda x: x.response, reverse=True)[:self.max_features]
            indices = [kp.class_id for kp in keypoints] if hasattr(keypoints[0], 'class_id') else list(range(len(keypoints)))
            descriptors = descriptors[indices] if descriptors is not None else None
        return keypoints, descriptors
    def get_detector_params(self) -> Dict:
        return {'type': 'SURF', 'max_features': self.max_features, 'hessian_threshold': self.hessian_threshold, 'n_octaves': self.n_octaves, 'n_octave_layers': self.n_octave_layers, 'extended': self.extended, 'upright': self.upright}
class FeatureMatcher(ABC):
    def __init__(self):
        self.matcher = None
    @abstractmethod
    def match(self, desc1: np.ndarray, desc2: np.ndarray) -> List:
        pass
    @abstractmethod
    def get_matcher_params(self) -> Dict:
        pass
class BruteForceMatcher(FeatureMatcher):
    def __init__(self, norm_type: int = cv2.NORM_HAMMING, cross_check: bool = True):
        super().__init__()
        self.norm_type = norm_type
        self.cross_check = cross_check
        self.matcher = cv2.BFMatcher(norm_type, cross_check)
    def match(self, desc1: np.ndarray, desc2: np.ndarray) -> List:
        if desc1 is None or desc2 is None:
            return []
        matches = self.matcher.match(desc1, desc2)
        return sorted(matches, key=lambda x: x.distance)
    def get_matcher_params(self) -> Dict:
        return {'type': 'BruteForce', 'norm_type': self.norm_type, 'cross_check': self.cross_check}
class FLANNMatcher(FeatureMatcher):
    def __init__(self, descriptor_type: str = 'ORB'):
        super().__init__()
        self.descriptor_type = descriptor_type
        if descriptor_type == 'ORB':
            FLANN_INDEX_LSH = 6
            index_params = dict(algorithm=FLANN_INDEX_LSH, table_number=6, key_size=12, multi_probe_level=1)
        else:
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
    def match(self, desc1: np.ndarray, desc2: np.ndarray) -> List:
        if desc1 is None or desc2 is None or len(desc1) < 2 or len(desc2) < 2:
            return []
        try:
            matches = self.matcher.knnMatch(desc1, desc2, k=2)
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
            return sorted(good_matches, key=lambda x: x.distance)
        except cv2.error:
            return []
    def get_matcher_params(self) -> Dict:
        return {'type': 'FLANN', 'descriptor_type': self.descriptor_type}
class OutlierRejection:
    @staticmethod
    def ransac_filter(kp1: List, kp2: List, matches: List, method: int = cv2.RANSAC, ransac_threshold: float = 3.0, confidence: float = 0.99) -> Tuple[List, np.ndarray]:
        if len(matches) < 4:
            return matches, np.ones(len(matches), dtype=bool)
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        try:
            M, mask = cv2.findHomography(src_pts, dst_pts, method, ransac_threshold, confidence=confidence)
            mask = mask.ravel().astype(bool)
            inlier_matches = [matches[i] for i in range(len(matches)) if mask[i]]
            return inlier_matches, mask
        except cv2.error:
            return matches, np.ones(len(matches), dtype=bool)
    @staticmethod
    def fundamental_matrix_filter(kp1: List, kp2: List, matches: List, method: int = cv2.FM_RANSAC, ransac_threshold: float = 1.0, confidence: float = 0.99) -> Tuple[List, np.ndarray]:
        if len(matches) < 8:
            return matches, np.ones(len(matches), dtype=bool)
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches])
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches])
        try:
            F, mask = cv2.findFundamentalMat(src_pts, dst_pts, method, ransac_threshold, confidence)
            mask = mask.ravel().astype(bool)
            inlier_matches = [matches[i] for i in range(len(matches)) if mask[i]]
            return inlier_matches, mask
        except cv2.error:
            return matches, np.ones(len(matches), dtype=bool)
    @staticmethod
    def distance_filter(matches: List, distance_threshold: float = 50.0) -> List:
        return [m for m in matches if m.distance <= distance_threshold]
    @staticmethod
    def ratio_test(matches: List, ratio: float = 0.7) -> List:
        good_matches = []
        for i in range(0, len(matches) - 1, 2):
            if i + 1 < len(matches):
                m1, m2 = matches[i], matches[i + 1]
                if m1.distance < ratio * m2.distance:
                    good_matches.append(m1)
        return good_matches
class FeatureTracker:
    def __init__(self, detector: FeatureDetector, matcher: FeatureMatcher, use_outlier_rejection: bool = True):
        self.detector = detector
        self.matcher = matcher
        self.use_outlier_rejection = use_outlier_rejection
        self.previous_keypoints = None
        self.previous_descriptors = None
        self.previous_image = None
    def track_features(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> Dict:
        keypoints, descriptors = self.detector.detect_and_compute(image, mask)
        result = {'keypoints': keypoints, 'descriptors': descriptors, 'matches': [], 'inlier_matches': [], 'inlier_ratio': 0.0}
        if self.previous_descriptors is not None and descriptors is not None:
            matches = self.matcher.match(self.previous_descriptors, descriptors)
            result['matches'] = matches
            if self.use_outlier_rejection and len(matches) > 8:
                inlier_matches, mask = OutlierRejection.fundamental_matrix_filter(self.previous_keypoints, keypoints, matches)
                result['inlier_matches'] = inlier_matches
                result['inlier_ratio'] = len(inlier_matches) / len(matches) if matches else 0.0
            else:
                result['inlier_matches'] = matches
                result['inlier_ratio'] = 1.0
        self.previous_keypoints = keypoints
        self.previous_descriptors = descriptors
        self.previous_image = image.copy()
        return result
    def reset(self):
        self.previous_keypoints = None
        self.previous_descriptors = None
        self.previous_image = None
    def get_matched_points(self, matches: List) -> Tuple[np.ndarray, np.ndarray]:
        if not matches or self.previous_keypoints is None:
            return np.array([]), np.array([])
        pts1 = np.float32([self.previous_keypoints[m.queryIdx].pt for m in matches])
        pts2 = np.float32([self.detector.detector.detect(self.previous_image)[m.trainIdx].pt for m in matches])
        return pts1, pts2
class FeatureVisualization:
    @staticmethod
    def draw_keypoints(image: np.ndarray, keypoints: List, color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        return cv2.drawKeypoints(image, keypoints, None, color=color, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    @staticmethod
    def draw_matches(img1: np.ndarray, kp1: List, img2: np.ndarray, kp2: List, matches: List, max_matches: int = 50) -> np.ndarray:
        if len(matches) > max_matches:
            matches = matches[:max_matches]
        return cv2.drawMatches(img1, kp1, img2, kp2, matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    @staticmethod
    def create_feature_statistics(keypoints: List, matches: List) -> Dict:
        if not keypoints:
            return {'num_keypoints': 0, 'num_matches': 0, 'avg_response': 0.0, 'response_std': 0.0}
        responses = [kp.response for kp in keypoints]
        return {'num_keypoints': len(keypoints), 'num_matches': len(matches), 'avg_response': np.mean(responses), 'response_std': np.std(responses), 'min_response': np.min(responses), 'max_response': np.max(responses)}