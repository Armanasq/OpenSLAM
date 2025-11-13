import numpy as np
from scipy.spatial.transform import Rotation
import config

def align_trajectories(estimated, ground_truth, method='auto'):
    est_poses = np.array(estimated)
    gt_poses = np.array(ground_truth)

    if method == 'auto':
        method = _choose_alignment_method(est_poses, gt_poses)

    if method == 'se3':
        return _align_se3(est_poses, gt_poses)
    elif method == 'sim3':
        return _align_sim3(est_poses, gt_poses)
    elif method == 'yaw_only':
        return _align_yaw(est_poses, gt_poses)
    else:
        return est_poses, np.eye(4), 1.0

def _choose_alignment_method(est_poses, gt_poses):
    est_scale = _estimate_trajectory_scale(est_poses)
    gt_scale = _estimate_trajectory_scale(gt_poses)

    scale_ratio = est_scale / gt_scale if gt_scale > 0 else 1.0

    if abs(scale_ratio - 1.0) > 0.1:
        return 'sim3'

    z_variance = np.var(est_poses[:, 2, 3]) if len(est_poses.shape) == 3 else 0
    if z_variance < 0.01:
        return 'yaw_only'

    return 'se3'

def _estimate_trajectory_scale(poses):
    if len(poses.shape) == 3:
        positions = poses[:, :3, 3]
    else:
        positions = poses[:, :3]

    if len(positions) < 2:
        return 1.0

    diffs = np.diff(positions, axis=0)
    distances = np.linalg.norm(diffs, axis=1)
    return np.sum(distances)

def _align_se3(est_poses, gt_poses):
    n = min(len(est_poses), len(gt_poses))

    if len(est_poses.shape) == 3:
        est_points = est_poses[:n, :3, 3]
    else:
        est_points = est_poses[:n, :3]

    if len(gt_poses.shape) == 3:
        gt_points = gt_poses[:n, :3, 3]
    else:
        gt_points = gt_poses[:n, :3]

    est_centroid = np.mean(est_points, axis=0)
    gt_centroid = np.mean(gt_points, axis=0)

    est_centered = est_points - est_centroid
    gt_centered = gt_points - gt_centroid

    H = est_centered.T @ gt_centered
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    t = gt_centroid - R @ est_centroid

    transform = np.eye(4)
    transform[:3, :3] = R
    transform[:3, 3] = t

    aligned = _apply_transform(est_poses, transform)

    return aligned, transform, 1.0

def _align_sim3(est_poses, gt_poses):
    n = min(len(est_poses), len(gt_poses))

    if len(est_poses.shape) == 3:
        est_points = est_poses[:n, :3, 3]
    else:
        est_points = est_poses[:n, :3]

    if len(gt_poses.shape) == 3:
        gt_points = gt_poses[:n, :3, 3]
    else:
        gt_points = gt_poses[:n, :3]

    est_centroid = np.mean(est_points, axis=0)
    gt_centroid = np.mean(gt_points, axis=0)

    est_centered = est_points - est_centroid
    gt_centered = gt_points - gt_centroid

    est_scale = np.sqrt(np.sum(est_centered ** 2) / n)
    gt_scale = np.sqrt(np.sum(gt_centered ** 2) / n)
    scale = gt_scale / est_scale if est_scale > 0 else 1.0

    est_scaled = est_centered * scale

    H = est_scaled.T @ gt_centered
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    t = gt_centroid - scale * R @ est_centroid

    transform = np.eye(4)
    transform[:3, :3] = scale * R
    transform[:3, 3] = t

    aligned = _apply_transform(est_poses, transform, scale=scale)

    return aligned, transform, scale

def _align_yaw(est_poses, gt_poses):
    n = min(len(est_poses), len(gt_poses))

    if len(est_poses.shape) == 3:
        est_points = est_poses[:n, :3, 3]
    else:
        est_points = est_poses[:n, :3]

    if len(gt_poses.shape) == 3:
        gt_points = gt_poses[:n, :3, 3]
    else:
        gt_points = gt_poses[:n, :3]

    est_centroid = np.mean(est_points[:, :2], axis=0)
    gt_centroid = np.mean(gt_points[:, :2], axis=0)

    est_centered = est_points[:, :2] - est_centroid
    gt_centered = gt_points[:, :2] - gt_centroid

    angles_est = np.arctan2(est_centered[:, 1], est_centered[:, 0])
    angles_gt = np.arctan2(gt_centered[:, 1], gt_centered[:, 0])
    yaw = np.median(angles_gt - angles_est)

    R = np.eye(3)
    R[:2, :2] = [[np.cos(yaw), -np.sin(yaw)], [np.sin(yaw), np.cos(yaw)]]

    t = np.zeros(3)
    t[:2] = gt_centroid - R[:2, :2] @ est_centroid

    transform = np.eye(4)
    transform[:3, :3] = R
    transform[:3, 3] = t

    aligned = _apply_transform(est_poses, transform)

    return aligned, transform, 1.0

def _apply_transform(poses, transform, scale=1.0):
    if len(poses.shape) == 3:
        aligned = np.zeros_like(poses)
        for i, pose in enumerate(poses):
            aligned[i] = transform @ pose
            if scale != 1.0:
                aligned[i][:3, 3] *= scale
        return aligned
    else:
        aligned = np.zeros_like(poses)
        for i, pos in enumerate(poses):
            point = np.ones(4)
            point[:3] = pos[:3]
            transformed = transform @ point
            aligned[i] = transformed[:3]
        return aligned

def compute_alignment_quality(aligned, ground_truth):
    n = min(len(aligned), len(ground_truth))

    if len(aligned.shape) == 3:
        aligned_points = aligned[:n, :3, 3]
    else:
        aligned_points = aligned[:n, :3]

    if len(ground_truth.shape) == 3:
        gt_points = ground_truth[:n, :3, 3]
    else:
        gt_points = ground_truth[:n, :3]

    errors = np.linalg.norm(aligned_points - gt_points, axis=1)

    return {'mean_error': float(np.mean(errors)), 'median_error': float(np.median(errors)), 'std_error': float(np.std(errors)), 'max_error': float(np.max(errors)), 'rmse': float(np.sqrt(np.mean(errors ** 2)))}

def synchronize_timestamps(est_timestamps, gt_timestamps, est_data, gt_data, max_diff=0.02):
    est_times = np.array(est_timestamps)
    gt_times = np.array(gt_timestamps)

    synchronized = []

    for i, et in enumerate(est_times):
        diffs = np.abs(gt_times - et)
        min_idx = np.argmin(diffs)

        if diffs[min_idx] < max_diff:
            synchronized.append({'est_idx': i, 'gt_idx': int(min_idx), 'est_time': float(et), 'gt_time': float(gt_times[min_idx]), 'time_diff': float(diffs[min_idx]), 'est_data': est_data[i], 'gt_data': gt_data[min_idx]})

    return synchronized
