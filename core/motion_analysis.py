import numpy as np
import openslam_config as cfg
from core.trajectory import extract_positions, extract_rotations, compute_velocities, compute_angular_velocities
def classify_motion(velocity, angular_velocity):
    if velocity < cfg.VELOCITY_THRESHOLD and angular_velocity < cfg.ANGULAR_VELOCITY_THRESHOLD:
        return 'stationary'
    if angular_velocity > cfg.ANGULAR_VELOCITY_THRESHOLD * 3:
        if angular_velocity > 0:
            return 'rotation_cw'
        else:
            return 'rotation_ccw'
    if velocity > cfg.VELOCITY_THRESHOLD:
        return 'forward'
    return 'other'
def analyze_motion_patterns(poses, timestamps):
    if timestamps is None:
        return None, 'timestamps_required'
    velocities, error = compute_velocities(poses, timestamps)
    if error:
        return None, error
    angular_vels, error = compute_angular_velocities(poses, timestamps)
    if error:
        return None, error
    motion_classes = []
    for i in range(len(velocities)):
        motion_classes.append(classify_motion(velocities[i], angular_vels[i]))
    motion_counts = {}
    for category in cfg.MOTION_CATEGORIES:
        motion_counts[category] = motion_classes.count(category)
    total = len(motion_classes)
    motion_percentages = {k: (v / total * 100) if total > 0 else 0 for k, v in motion_counts.items()}
    dominant_motion = max(motion_counts.items(), key=lambda x: x[1])[0] if total > 0 else 'unknown'
    return {'counts': motion_counts, 'percentages': motion_percentages, 'dominant': dominant_motion, 'classes': motion_classes}, None
def segment_by_motion(poses, timestamps, min_segment_length=10):
    if timestamps is None:
        return None, 'timestamps_required'
    motion_result, error = analyze_motion_patterns(poses, timestamps)
    if error:
        return None, error
    motion_classes = motion_result['classes']
    segments = []
    if len(motion_classes) == 0:
        return {'segments': []}, None
    current_class = motion_classes[0]
    start_idx = 0
    for i in range(1, len(motion_classes)):
        if motion_classes[i] != current_class:
            if i - start_idx >= min_segment_length:
                segments.append({'start': start_idx, 'end': i - 1, 'type': current_class, 'length': i - start_idx})
            current_class = motion_classes[i]
            start_idx = i
    if len(motion_classes) - start_idx >= min_segment_length:
        segments.append({'start': start_idx, 'end': len(motion_classes) - 1, 'type': current_class, 'length': len(motion_classes) - start_idx})
    return {'segments': segments, 'num_segments': len(segments)}, None
def compute_accelerations(poses, timestamps):
    if timestamps is None:
        return None, 'timestamps_required'
    velocities, error = compute_velocities(poses, timestamps)
    if error:
        return None, error
    accelerations = np.zeros(len(velocities))
    for i in range(1, len(velocities)):
        dt = timestamps[i] - timestamps[i-1]
        if dt > 0:
            accelerations[i] = (velocities[i] - velocities[i-1]) / dt
    return accelerations, None
def analyze_dynamics(poses, timestamps):
    if timestamps is None:
        return None, 'timestamps_required'
    velocities, error = compute_velocities(poses, timestamps)
    if error:
        return None, error
    accelerations, error = compute_accelerations(poses, timestamps)
    if error:
        return None, error
    angular_vels, error = compute_angular_velocities(poses, timestamps)
    if error:
        return None, error
    vel_stats = {'mean': np.mean(velocities[velocities > 0]) if np.any(velocities > 0) else 0, 'max': np.max(velocities), 'std': np.std(velocities)}
    acc_stats = {'mean': np.mean(np.abs(accelerations[accelerations != 0])) if np.any(accelerations != 0) else 0, 'max': np.max(np.abs(accelerations)), 'std': np.std(accelerations)}
    ang_stats = {'mean': np.mean(angular_vels[angular_vels > 0]) if np.any(angular_vels > 0) else 0, 'max': np.max(angular_vels), 'std': np.std(angular_vels)}
    return {'velocity': vel_stats, 'acceleration': acc_stats, 'angular_velocity': ang_stats}, None
def compute_path_efficiency(poses):
    positions = extract_positions(poses)
    if positions is None:
        return None, 'invalid_pose_format'
    total_distance = 0
    for i in range(1, len(positions)):
        total_distance += np.linalg.norm(positions[i] - positions[i-1])
    straight_line_distance = np.linalg.norm(positions[-1] - positions[0])
    efficiency = straight_line_distance / total_distance if total_distance > 0 else 0
    return {'total_distance': total_distance, 'straight_line_distance': straight_line_distance, 'efficiency': efficiency}, None
