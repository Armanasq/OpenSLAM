import numpy as np
from scipy.spatial import cKDTree
from core.trajectory import extract_positions
def align_icp(source_points, target_points, max_iterations=50, tolerance=1e-6):
    if len(source_points) < 3 or len(target_points) < 3:
        return None, 'insufficient_points'
    current_source = source_points.copy()
    previous_error = float('inf')
    R_total = np.eye(3)
    t_total = np.zeros(3)
    for iteration in range(max_iterations):
        tree = cKDTree(target_points)
        distances, indices = tree.query(current_source)
        correspondences = target_points[indices]
        source_centroid = np.mean(current_source, axis=0)
        target_centroid = np.mean(correspondences, axis=0)
        source_centered = current_source - source_centroid
        target_centered = correspondences - target_centroid
        H = source_centered.T @ target_centered
        U, S, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T
        t = target_centroid - R @ source_centroid
        current_source = (R @ current_source.T).T + t
        R_total = R @ R_total
        t_total = R @ t_total + t
        error = np.mean(distances)
        if abs(previous_error - error) < tolerance:
            break
        previous_error = error
    transform = np.eye(4)
    transform[:3, :3] = R_total
    transform[:3, 3] = t_total
    return {'transform': transform, 'rotation': R_total, 'translation': t_total, 'final_error': float(error), 'iterations': iteration + 1}, None
def align_ransac(source_points, target_points, num_iterations=1000, inlier_threshold=0.1, min_inliers=10):
    if len(source_points) < 3 or len(target_points) < 3:
        return None, 'insufficient_points'
    if len(source_points) != len(target_points):
        return None, 'point_count_mismatch'
    best_inliers = []
    best_transform = None
    best_error = float('inf')
    for iteration in range(num_iterations):
        sample_indices = np.random.choice(len(source_points), 3, replace=False)
        source_sample = source_points[sample_indices]
        target_sample = target_points[sample_indices]
        source_centroid = np.mean(source_sample, axis=0)
        target_centroid = np.mean(target_sample, axis=0)
        source_centered = source_sample - source_centroid
        target_centered = target_sample - target_centroid
        H = source_centered.T @ target_centered
        U, S, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T
        t = target_centroid - R @ source_centroid
        transformed = (R @ source_points.T).T + t
        errors = np.linalg.norm(transformed - target_points, axis=1)
        inliers = np.where(errors < inlier_threshold)[0]
        if len(inliers) > len(best_inliers):
            best_inliers = inliers
            best_transform = (R, t)
            best_error = np.mean(errors[inliers])
    if len(best_inliers) < min_inliers:
        return None, 'insufficient_inliers'
    R, t = best_transform
    transform = np.eye(4)
    transform[:3, :3] = R
    transform[:3, 3] = t
    inlier_ratio = len(best_inliers) / len(source_points)
    return {'transform': transform, 'rotation': R, 'translation': t, 'inliers': best_inliers.tolist(), 'inlier_count': len(best_inliers), 'inlier_ratio': float(inlier_ratio), 'mean_error': float(best_error)}, None
def align_umeyama(source_points, target_points, estimate_scale=True):
    if len(source_points) < 2 or len(target_points) < 2:
        return None, 'insufficient_points'
    if len(source_points) != len(target_points):
        return None, 'point_count_mismatch'
    source_centroid = np.mean(source_points, axis=0)
    target_centroid = np.mean(target_points, axis=0)
    source_centered = source_points - source_centroid
    target_centered = target_points - target_centroid
    source_var = np.mean(np.sum(source_centered ** 2, axis=1))
    H = source_centered.T @ target_centered / len(source_points)
    U, D, Vt = np.linalg.svd(H)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    if estimate_scale:
        target_var = np.mean(np.sum(target_centered ** 2, axis=1))
        scale = target_var / source_var if source_var > 0 else 1.0
    else:
        scale = 1.0
    t = target_centroid - scale * R @ source_centroid
    transform = np.eye(4)
    transform[:3, :3] = scale * R
    transform[:3, 3] = t
    return {'transform': transform, 'rotation': R, 'translation': t, 'scale': float(scale)}, None
def align_poses_icp(source_poses, target_poses, max_iterations=50, tolerance=1e-6):
    if len(source_poses) != len(target_poses):
        return None, 'length_mismatch'
    source_positions = extract_positions(source_poses)
    target_positions = extract_positions(target_poses)
    if source_positions is None or target_positions is None:
        return None, 'invalid_pose_format'
    result, error = align_icp(source_positions, target_positions, max_iterations=max_iterations, tolerance=tolerance)
    if error:
        return None, error
    aligned_poses = apply_transform_to_poses(source_poses, result['transform'])
    return {'aligned_poses': aligned_poses, 'transform': result['transform'], 'rotation': result['rotation'], 'translation': result['translation'], 'final_error': result['final_error'], 'iterations': result['iterations']}, None
def align_poses_ransac(source_poses, target_poses, num_iterations=1000, inlier_threshold=0.1, min_inliers=10):
    if len(source_poses) != len(target_poses):
        return None, 'length_mismatch'
    source_positions = extract_positions(source_poses)
    target_positions = extract_positions(target_poses)
    if source_positions is None or target_positions is None:
        return None, 'invalid_pose_format'
    result, error = align_ransac(source_positions, target_positions, num_iterations=num_iterations, inlier_threshold=inlier_threshold, min_inliers=min_inliers)
    if error:
        return None, error
    aligned_poses = apply_transform_to_poses(source_poses, result['transform'])
    return {'aligned_poses': aligned_poses, 'transform': result['transform'], 'rotation': result['rotation'], 'translation': result['translation'], 'inliers': result['inliers'], 'inlier_count': result['inlier_count'], 'inlier_ratio': result['inlier_ratio'], 'mean_error': result['mean_error']}, None
def apply_transform_to_poses(poses, transform):
    aligned_poses = []
    for pose in poses:
        aligned_pose = transform @ pose
        aligned_poses.append(aligned_pose)
    return np.array(aligned_poses)
