import sys
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from collections import defaultdict
import heapq
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
@dataclass
class Landmark:
    id: int
    position: np.ndarray
    observations: List[Tuple[int, np.ndarray]]
    covariance: np.ndarray
    descriptor: Optional[np.ndarray] = None
    first_observed_frame: int = 0
    last_observed_frame: int = 0
@dataclass
class KeyFrame:
    id: int
    timestamp: float
    pose: np.ndarray
    covariance: np.ndarray
    keypoints: List
    descriptors: np.ndarray
    landmark_observations: Dict[int, np.ndarray]
    connected_keyframes: Set[int]
@dataclass
class LoopClosure:
    query_frame_id: int
    match_frame_id: int
    relative_pose: np.ndarray
    confidence: float
    matches: List[Tuple[int, int]]
    timestamp: float
class PoseGraph:
    def __init__(self):
        self.keyframes = {}
        self.landmarks = {}
        self.edges = []
        self.loop_closures = []
        self.next_keyframe_id = 0
        self.next_landmark_id = 0
    def add_keyframe(self, timestamp: float, pose: np.ndarray, covariance: np.ndarray, keypoints: List, descriptors: np.ndarray) -> int:
        keyframe_id = self.next_keyframe_id
        self.next_keyframe_id += 1
        keyframe = KeyFrame(id=keyframe_id, timestamp=timestamp, pose=pose.copy(), covariance=covariance.copy(), keypoints=keypoints, descriptors=descriptors, landmark_observations={}, connected_keyframes=set())
        self.keyframes[keyframe_id] = keyframe
        return keyframe_id
    def add_landmark(self, position: np.ndarray, covariance: np.ndarray, descriptor: Optional[np.ndarray] = None) -> int:
        landmark_id = self.next_landmark_id
        self.next_landmark_id += 1
        landmark = Landmark(id=landmark_id, position=position.copy(), observations=[], covariance=covariance.copy(), descriptor=descriptor)
        self.landmarks[landmark_id] = landmark
        return landmark_id
    def add_observation(self, keyframe_id: int, landmark_id: int, observation: np.ndarray):
        if keyframe_id in self.keyframes and landmark_id in self.landmarks:
            self.keyframes[keyframe_id].landmark_observations[landmark_id] = observation
            self.landmarks[landmark_id].observations.append((keyframe_id, observation))
            if not self.landmarks[landmark_id].first_observed_frame:
                self.landmarks[landmark_id].first_observed_frame = keyframe_id
            self.landmarks[landmark_id].last_observed_frame = keyframe_id
    def add_edge(self, keyframe1_id: int, keyframe2_id: int, relative_pose: np.ndarray, information_matrix: np.ndarray):
        edge = {'from': keyframe1_id, 'to': keyframe2_id, 'relative_pose': relative_pose, 'information': information_matrix}
        self.edges.append(edge)
        if keyframe1_id in self.keyframes and keyframe2_id in self.keyframes:
            self.keyframes[keyframe1_id].connected_keyframes.add(keyframe2_id)
            self.keyframes[keyframe2_id].connected_keyframes.add(keyframe1_id)
    def add_loop_closure(self, query_frame_id: int, match_frame_id: int, relative_pose: np.ndarray, confidence: float, matches: List[Tuple[int, int]]):
        loop_closure = LoopClosure(query_frame_id=query_frame_id, match_frame_id=match_frame_id, relative_pose=relative_pose, confidence=confidence, matches=matches, timestamp=self.keyframes[query_frame_id].timestamp if query_frame_id in self.keyframes else 0.0)
        self.loop_closures.append(loop_closure)
        information_matrix = np.eye(6) * confidence
        self.add_edge(query_frame_id, match_frame_id, relative_pose, information_matrix)
    def get_keyframe_poses(self) -> Dict[int, np.ndarray]:
        return {kf_id: kf.pose for kf_id, kf in self.keyframes.items()}
    def get_landmark_positions(self) -> Dict[int, np.ndarray]:
        return {lm_id: lm.position for lm_id, lm in self.landmarks.items()}
    def get_covisible_keyframes(self, keyframe_id: int, min_observations: int = 5) -> List[int]:
        if keyframe_id not in self.keyframes:
            return []
        keyframe = self.keyframes[keyframe_id]
        covisible_counts = defaultdict(int)
        for landmark_id in keyframe.landmark_observations:
            if landmark_id in self.landmarks:
                for obs_kf_id, _ in self.landmarks[landmark_id].observations:
                    if obs_kf_id != keyframe_id:
                        covisible_counts[obs_kf_id] += 1
        return [kf_id for kf_id, count in covisible_counts.items() if count >= min_observations]
class LoopDetector:
    def __init__(self, similarity_threshold: float = 0.7, temporal_consistency_window: int = 3, min_feature_matches: int = 20):
        self.similarity_threshold = similarity_threshold
        self.temporal_consistency_window = temporal_consistency_window
        self.min_feature_matches = min_feature_matches
        self.keyframe_descriptors = {}
        self.bow_database = {}
        self.vocabulary = None
    def set_vocabulary(self, vocabulary: np.ndarray):
        self.vocabulary = vocabulary
    def compute_bow_histogram(self, descriptors: np.ndarray) -> np.ndarray:
        if self.vocabulary is None or descriptors is None:
            return np.zeros(1000)
        from sklearn.metrics.pairwise import euclidean_distances
        distances = euclidean_distances(descriptors, self.vocabulary)
        closest_words = np.argmin(distances, axis=1)
        histogram = np.bincount(closest_words, minlength=len(self.vocabulary))
        return histogram / (np.linalg.norm(histogram) + 1e-8)
    def add_keyframe(self, keyframe_id: int, descriptors: np.ndarray):
        bow_histogram = self.compute_bow_histogram(descriptors)
        self.keyframe_descriptors[keyframe_id] = descriptors
        self.bow_database[keyframe_id] = bow_histogram
    def detect_loop_closure(self, query_keyframe_id: int, exclude_recent_frames: int = 50) -> Optional[Tuple[int, float]]:
        if query_keyframe_id not in self.bow_database:
            return None
        query_histogram = self.bow_database[query_keyframe_id]
        best_match = None
        best_similarity = 0.0
        for candidate_id, candidate_histogram in self.bow_database.items():
            if abs(candidate_id - query_keyframe_id) <= exclude_recent_frames:
                continue
            similarity = self._compute_similarity(query_histogram, candidate_histogram)
            if similarity > best_similarity and similarity > self.similarity_threshold:
                best_similarity = similarity
                best_match = candidate_id
        if best_match is not None:
            temporal_consistency = self._check_temporal_consistency(query_keyframe_id, best_match)
            if temporal_consistency:
                return best_match, best_similarity
        return None
    def _compute_similarity(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        dot_product = np.dot(hist1, hist2)
        return dot_product
    def _check_temporal_consistency(self, query_id: int, match_id: int) -> bool:
        consistent_matches = 0
        for i in range(1, self.temporal_consistency_window + 1):
            prev_query_id = query_id - i
            if prev_query_id in self.bow_database:
                prev_query_hist = self.bow_database[prev_query_id]
                for j in range(-2, 3):
                    candidate_id = match_id + j
                    if candidate_id in self.bow_database:
                        candidate_hist = self.bow_database[candidate_id]
                        similarity = self._compute_similarity(prev_query_hist, candidate_hist)
                        if similarity > self.similarity_threshold * 0.8:
                            consistent_matches += 1
                            break
        return consistent_matches >= self.temporal_consistency_window // 2
    def verify_loop_closure(self, query_keyframe_id: int, match_keyframe_id: int) -> Optional[Tuple[np.ndarray, List[Tuple[int, int]]]]:
        if query_keyframe_id not in self.keyframe_descriptors or match_keyframe_id not in self.keyframe_descriptors:
            return None
        query_desc = self.keyframe_descriptors[query_keyframe_id]
        match_desc = self.keyframe_descriptors[match_keyframe_id]
        matches = self._match_descriptors(query_desc, match_desc)
        if len(matches) < self.min_feature_matches:
            return None
        try:
            relative_pose = self._estimate_relative_pose(matches, query_keyframe_id, match_keyframe_id)
            return relative_pose, matches
        except:
            return None
    def _match_descriptors(self, desc1: np.ndarray, desc2: np.ndarray) -> List[Tuple[int, int]]:
        import cv2
        if desc1 is None or desc2 is None:
            return []
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = matcher.match(desc1, desc2)
        matches = sorted(matches, key=lambda x: x.distance)
        good_matches = [m for m in matches if m.distance < 50]
        return [(m.queryIdx, m.trainIdx) for m in good_matches]
    def _estimate_relative_pose(self, matches: List[Tuple[int, int]], query_id: int, match_id: int) -> np.ndarray:
        return np.eye(4)
class PoseGraphOptimizer:
    def __init__(self, max_iterations: int = 100, convergence_threshold: float = 1e-6):
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
    def optimize(self, pose_graph: PoseGraph) -> Dict:
        poses = pose_graph.get_keyframe_poses()
        landmarks = pose_graph.get_landmark_positions()
        if len(poses) < 2:
            return {'success': False, 'error': 'Insufficient poses for optimization'}
        optimized_poses = self._gauss_newton_optimization(poses, landmarks, pose_graph.edges)
        for kf_id, optimized_pose in optimized_poses.items():
            if kf_id in pose_graph.keyframes:
                pose_graph.keyframes[kf_id].pose = optimized_pose
        return {'success': True, 'iterations': self.max_iterations, 'final_error': 0.0, 'optimized_poses': len(optimized_poses)}
    def _gauss_newton_optimization(self, poses: Dict[int, np.ndarray], landmarks: Dict[int, np.ndarray], edges: List[Dict]) -> Dict[int, np.ndarray]:
        optimized_poses = {k: v.copy() for k, v in poses.items()}
        for iteration in range(self.max_iterations):
            H, b = self._build_linear_system(optimized_poses, landmarks, edges)
            if H.size == 0:
                break
            try:
                delta = np.linalg.solve(H, -b)
                self._update_poses(optimized_poses, delta)
                if np.linalg.norm(delta) < self.convergence_threshold:
                    break
            except np.linalg.LinAlgError:
                break
        return optimized_poses
    def _build_linear_system(self, poses: Dict[int, np.ndarray], landmarks: Dict[int, np.ndarray], edges: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        num_poses = len(poses)
        if num_poses == 0:
            return np.array([]), np.array([])
        H = np.zeros((num_poses * 6, num_poses * 6))
        b = np.zeros(num_poses * 6)
        pose_ids = sorted(poses.keys())
        id_to_index = {pose_id: i for i, pose_id in enumerate(pose_ids)}
        for edge in edges:
            from_id = edge['from']
            to_id = edge['to']
            if from_id not in id_to_index or to_id not in id_to_index:
                continue
            from_idx = id_to_index[from_id]
            to_idx = id_to_index[to_id]
            relative_pose = edge['relative_pose']
            information = edge['information']
            error = self._compute_pose_error(poses[from_id], poses[to_id], relative_pose)
            jacobian_from, jacobian_to = self._compute_pose_jacobians(poses[from_id], poses[to_id], relative_pose)
            H[from_idx*6:(from_idx+1)*6, from_idx*6:(from_idx+1)*6] += jacobian_from.T @ information @ jacobian_from
            H[to_idx*6:(to_idx+1)*6, to_idx*6:(to_idx+1)*6] += jacobian_to.T @ information @ jacobian_to
            H[from_idx*6:(from_idx+1)*6, to_idx*6:(to_idx+1)*6] += jacobian_from.T @ information @ jacobian_to
            H[to_idx*6:(to_idx+1)*6, from_idx*6:(from_idx+1)*6] += jacobian_to.T @ information @ jacobian_from
            b[from_idx*6:(from_idx+1)*6] += jacobian_from.T @ information @ error
            b[to_idx*6:(to_idx+1)*6] += jacobian_to.T @ information @ error
        return H, b
    def _compute_pose_error(self, pose1: np.ndarray, pose2: np.ndarray, relative_pose: np.ndarray) -> np.ndarray:
        predicted_relative = np.linalg.inv(pose1) @ pose2
        error_matrix = np.linalg.inv(relative_pose) @ predicted_relative
        translation_error = error_matrix[:3, 3]
        rotation_error = self._rotation_matrix_to_axis_angle(error_matrix[:3, :3])
        return np.concatenate([translation_error, rotation_error])
    def _compute_pose_jacobians(self, pose1: np.ndarray, pose2: np.ndarray, relative_pose: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        jacobian_from = -np.eye(6)
        jacobian_to = np.eye(6)
        return jacobian_from, jacobian_to
    def _rotation_matrix_to_axis_angle(self, R: np.ndarray) -> np.ndarray:
        trace = np.trace(R)
        angle = np.arccos(np.clip((trace - 1) / 2, -1, 1))
        if angle < 1e-6:
            return np.zeros(3)
        axis = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * np.sin(angle))
        return axis * angle
    def _update_poses(self, poses: Dict[int, np.ndarray], delta: np.ndarray):
        pose_ids = sorted(poses.keys())
        for i, pose_id in enumerate(pose_ids):
            delta_pose = delta[i*6:(i+1)*6]
            delta_translation = delta_pose[:3]
            delta_rotation = self._axis_angle_to_rotation_matrix(delta_pose[3:])
            poses[pose_id][:3, 3] += delta_translation
            poses[pose_id][:3, :3] = poses[pose_id][:3, :3] @ delta_rotation
    def _axis_angle_to_rotation_matrix(self, axis_angle: np.ndarray) -> np.ndarray:
        angle = np.linalg.norm(axis_angle)
        if angle < 1e-8:
            return np.eye(3)
        axis = axis_angle / angle
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K
class SLAMBackend:
    def __init__(self, loop_detection_enabled: bool = True, optimization_frequency: int = 10):
        self.pose_graph = PoseGraph()
        self.loop_detector = LoopDetector()
        self.optimizer = PoseGraphOptimizer()
        self.loop_detection_enabled = loop_detection_enabled
        self.optimization_frequency = optimization_frequency
        self.frame_count = 0
        self.last_optimization_frame = 0
    def add_keyframe(self, timestamp: float, pose: np.ndarray, covariance: np.ndarray, keypoints: List, descriptors: np.ndarray, landmarks: List[Tuple[np.ndarray, np.ndarray]]) -> int:
        keyframe_id = self.pose_graph.add_keyframe(timestamp, pose, covariance, keypoints, descriptors)
        for landmark_pos, landmark_cov in landmarks:
            landmark_id = self.pose_graph.add_landmark(landmark_pos, landmark_cov)
            observation = np.array([0.0, 0.0])
            self.pose_graph.add_observation(keyframe_id, landmark_id, observation)
        if keyframe_id > 0:
            prev_keyframe_id = keyframe_id - 1
            if prev_keyframe_id in self.pose_graph.keyframes:
                relative_pose = np.linalg.inv(self.pose_graph.keyframes[prev_keyframe_id].pose) @ pose
                information_matrix = np.eye(6)
                self.pose_graph.add_edge(prev_keyframe_id, keyframe_id, relative_pose, information_matrix)
        if self.loop_detection_enabled:
            self.loop_detector.add_keyframe(keyframe_id, descriptors)
            loop_result = self.loop_detector.detect_loop_closure(keyframe_id)
            if loop_result:
                match_id, confidence = loop_result
                verification = self.loop_detector.verify_loop_closure(keyframe_id, match_id)
                if verification:
                    relative_pose, matches = verification
                    self.pose_graph.add_loop_closure(keyframe_id, match_id, relative_pose, confidence, matches)
        self.frame_count += 1
        if self.frame_count - self.last_optimization_frame >= self.optimization_frequency:
            self._optimize_pose_graph()
            self.last_optimization_frame = self.frame_count
        return keyframe_id
    def _optimize_pose_graph(self):
        if len(self.pose_graph.keyframes) > 2:
            self.optimizer.optimize(self.pose_graph)
    def get_current_trajectory(self) -> List[np.ndarray]:
        poses = []
        for kf_id in sorted(self.pose_graph.keyframes.keys()):
            poses.append(self.pose_graph.keyframes[kf_id].pose)
        return poses
    def get_map_landmarks(self) -> List[np.ndarray]:
        return [landmark.position for landmark in self.pose_graph.landmarks.values()]
    def get_loop_closures(self) -> List[LoopClosure]:
        return self.pose_graph.loop_closures.copy()
    def get_statistics(self) -> Dict:
        return {'num_keyframes': len(self.pose_graph.keyframes), 'num_landmarks': len(self.pose_graph.landmarks), 'num_edges': len(self.pose_graph.edges), 'num_loop_closures': len(self.pose_graph.loop_closures), 'frames_processed': self.frame_count}
    def set_loop_detection_vocabulary(self, vocabulary: np.ndarray):
        self.loop_detector.set_vocabulary(vocabulary)
    def reset(self):
        self.pose_graph = PoseGraph()
        self.loop_detector = LoopDetector()
        self.frame_count = 0
        self.last_optimization_frame = 0