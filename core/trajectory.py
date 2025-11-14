import numpy as np
from config import openslam_config as cfg
def extract_positions(poses):
    if poses.shape[1:] == (4, 4):
        return poses[:, :3, 3]
    return None
def extract_rotations(poses):
    if poses.shape[1:] == (4, 4):
        return poses[:, :3, :3]
    return None
def compute_transform_se3(source_points, target_points):
    if source_points.shape != target_points.shape:
        return None, 'shape_mismatch'
    if source_points.shape[0] < 3:
        return None, 'insufficient_points'
    source_centroid = np.mean(source_points, axis=0)
    target_centroid = np.mean(target_points, axis=0)
    source_centered = source_points - source_centroid
    target_centered = target_points - target_centroid
    H = source_centered.T @ target_centered
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T
    t = target_centroid - R @ source_centroid
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T, None
def compute_transform_sim3(source_points, target_points):
    if source_points.shape != target_points.shape:
        return None, 'shape_mismatch'
    if source_points.shape[0] < 3:
        return None, 'insufficient_points'
    source_centroid = np.mean(source_points, axis=0)
    target_centroid = np.mean(target_points, axis=0)
    source_centered = source_points - source_centroid
    target_centered = target_points - target_centroid
    source_scale = np.sqrt(np.sum(source_centered ** 2) / len(source_centered))
    target_scale = np.sqrt(np.sum(target_centered ** 2) / len(target_centered))
    scale = target_scale / source_scale if source_scale > 0 else 1.0
    H = source_centered.T @ target_centered
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T
    t = target_centroid - scale * R @ source_centroid
    T = np.eye(4)
    T[:3, :3] = scale * R
    T[:3, 3] = t
    return {'transform': T, 'scale': scale, 'rotation': R, 'translation': t}, None
def align_trajectories(source_poses, target_poses, method='sim3'):
    if method not in cfg.ALIGNMENT_METHODS:
        return None, 'invalid_alignment_method'
    if len(source_poses) != len(target_poses):
        return None, 'length_mismatch'
    source_positions = extract_positions(source_poses)
    target_positions = extract_positions(target_poses)
    if source_positions is None or target_positions is None:
        return None, 'invalid_pose_format'
    if method == 'se3':
        transform, error = compute_transform_se3(source_positions, target_positions)
    elif method == 'sim3':
        result, error = compute_transform_sim3(source_positions, target_positions)
        if error:
            return None, error
        transform = result['transform']
    elif method == 'yaw_only':
        return None, 'yaw_only_not_implemented'
    elif method == 'auto':
        result, error = compute_transform_sim3(source_positions, target_positions)
        if error:
            return None, error
        if abs(result['scale'] - 1.0) < 0.01:
            method = 'se3'
            transform, error = compute_transform_se3(source_positions, target_positions)
        else:
            transform = result['transform']
    else:
        return None, 'unsupported_alignment_method'
    if transform is None:
        return None, 'alignment_failed'
    aligned_poses = np.array([transform @ pose for pose in source_poses])
    return {'aligned_poses': aligned_poses, 'transform': transform, 'method': method}, None
def synchronize_trajectories(traj1_timestamps, traj1_poses, traj2_timestamps, traj2_poses, max_offset=0.02):
    if len(traj1_timestamps) == 0 or len(traj2_timestamps) == 0:
        return None, 'empty_trajectory'
    synced_indices_1 = []
    synced_indices_2 = []
    j = 0
    for i, t1 in enumerate(traj1_timestamps):
        while j < len(traj2_timestamps) and traj2_timestamps[j] < t1 - max_offset:
            j += 1
        if j >= len(traj2_timestamps):
            break
        if abs(traj2_timestamps[j] - t1) <= max_offset:
            synced_indices_1.append(i)
            synced_indices_2.append(j)
    if len(synced_indices_1) == 0:
        return None, 'no_synchronized_frames'
    synced_traj1 = {'timestamps': traj1_timestamps[synced_indices_1], 'poses': traj1_poses[synced_indices_1]}
    synced_traj2 = {'timestamps': traj2_timestamps[synced_indices_2], 'poses': traj2_poses[synced_indices_2]}
    return {'traj1': synced_traj1, 'traj2': synced_traj2, 'num_matches': len(synced_indices_1)}, None
def interpolate_pose(pose1, pose2, alpha):
    if not (0 <= alpha <= 1):
        return None, 'invalid_alpha'
    t1 = pose1[:3, 3]
    t2 = pose2[:3, 3]
    t_interp = (1 - alpha) * t1 + alpha * t2
    R1 = pose1[:3, :3]
    R2 = pose2[:3, :3]
    R_delta = R1.T @ R2
    trace = np.trace(R_delta)
    if trace >= 3.0:
        R_interp = R1
    else:
        angle = np.arccos((trace - 1) / 2)
        if angle < 1e-6:
            R_interp = R1
        else:
            axis = np.array([R_delta[2,1] - R_delta[1,2], R_delta[0,2] - R_delta[2,0], R_delta[1,0] - R_delta[0,1]])
            axis = axis / (2 * np.sin(angle))
            angle_interp = alpha * angle
            K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
            R_interp_delta = np.eye(3) + np.sin(angle_interp) * K + (1 - np.cos(angle_interp)) * (K @ K)
            R_interp = R1 @ R_interp_delta
    pose_interp = np.eye(4)
    pose_interp[:3, :3] = R_interp
    pose_interp[:3, 3] = t_interp
    return pose_interp, None
def compute_distances(poses):
    positions = extract_positions(poses)
    if positions is None:
        return None, 'invalid_pose_format'
    distances = np.zeros(len(positions))
    for i in range(1, len(positions)):
        distances[i] = distances[i-1] + np.linalg.norm(positions[i] - positions[i-1])
    return distances, None
def compute_velocities(poses, timestamps):
    if len(poses) != len(timestamps):
        return None, 'length_mismatch'
    if len(poses) < 2:
        return None, 'insufficient_data'
    positions = extract_positions(poses)
    if positions is None:
        return None, 'invalid_pose_format'
    velocities = np.zeros(len(positions))
    for i in range(1, len(positions)):
        dt = timestamps[i] - timestamps[i-1]
        if dt > 0:
            velocities[i] = np.linalg.norm(positions[i] - positions[i-1]) / dt
    return velocities, None
def compute_angular_velocities(poses, timestamps):
    if len(poses) != len(timestamps):
        return None, 'length_mismatch'
    if len(poses) < 2:
        return None, 'insufficient_data'
    rotations = extract_rotations(poses)
    if rotations is None:
        return None, 'invalid_pose_format'
    angular_velocities = np.zeros(len(rotations))
    for i in range(1, len(rotations)):
        dt = timestamps[i] - timestamps[i-1]
        if dt > 0:
            R_delta = rotations[i-1].T @ rotations[i]
            trace = np.trace(R_delta)
            angle = np.arccos(np.clip((trace - 1) / 2, -1.0, 1.0))
            angular_velocities[i] = angle / dt
    return angular_velocities, None
