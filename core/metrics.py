import numpy as np
import openslam_config as cfg
from core.trajectory import extract_positions, extract_rotations
def compute_ate(estimated_poses, ground_truth_poses):
    if len(estimated_poses) != len(ground_truth_poses):
        return None, 'length_mismatch'
    if len(estimated_poses) == 0:
        return None, 'empty_trajectory'
    est_positions = extract_positions(estimated_poses)
    gt_positions = extract_positions(ground_truth_poses)
    if est_positions is None or gt_positions is None:
        return None, 'invalid_pose_format'
    errors = np.linalg.norm(est_positions - gt_positions, axis=1)
    rmse = np.sqrt(np.mean(errors ** 2))
    mean = np.mean(errors)
    median = np.median(errors)
    std = np.std(errors)
    max_error = np.max(errors)
    min_error = np.min(errors)
    return {'rmse': rmse, 'mean': mean, 'median': median, 'std': std, 'max': max_error, 'min': min_error, 'errors': errors}, None
def compute_relative_pose_error(pose1, pose2):
    if pose1.shape != (4, 4) or pose2.shape != (4, 4):
        return None, 'invalid_pose_shape'
    relative_pose = np.linalg.inv(pose1) @ pose2
    translation_error = np.linalg.norm(relative_pose[:3, 3])
    rotation_matrix = relative_pose[:3, :3]
    trace = np.trace(rotation_matrix)
    rotation_error = np.arccos(np.clip((trace - 1) / 2, -1.0, 1.0))
    rotation_error_deg = np.degrees(rotation_error)
    return {'translation': translation_error, 'rotation': rotation_error_deg}, None
def compute_rpe(estimated_poses, ground_truth_poses, delta=1.0, unit='frames'):
    if len(estimated_poses) != len(ground_truth_poses):
        return None, 'length_mismatch'
    if len(estimated_poses) < 2:
        return None, 'insufficient_data'
    if unit == 'frames':
        step = int(delta)
    elif unit == 'meters':
        return None, 'meters_unit_not_implemented'
    elif unit == 'seconds':
        return None, 'seconds_unit_not_implemented'
    else:
        return None, 'invalid_unit'
    translation_errors = []
    rotation_errors = []
    for i in range(len(estimated_poses) - step):
        est_relative = np.linalg.inv(estimated_poses[i]) @ estimated_poses[i + step]
        gt_relative = np.linalg.inv(ground_truth_poses[i]) @ ground_truth_poses[i + step]
        error_pose = np.linalg.inv(gt_relative) @ est_relative
        trans_error = np.linalg.norm(error_pose[:3, 3])
        rotation_matrix = error_pose[:3, :3]
        trace = np.trace(rotation_matrix)
        rot_error = np.arccos(np.clip((trace - 1) / 2, -1.0, 1.0))
        rot_error_deg = np.degrees(rot_error)
        translation_errors.append(trans_error)
        rotation_errors.append(rot_error_deg)
    translation_errors = np.array(translation_errors)
    rotation_errors = np.array(rotation_errors)
    trans_rmse = np.sqrt(np.mean(translation_errors ** 2))
    trans_mean = np.mean(translation_errors)
    trans_median = np.median(translation_errors)
    trans_std = np.std(translation_errors)
    rot_rmse = np.sqrt(np.mean(rotation_errors ** 2))
    rot_mean = np.mean(rotation_errors)
    rot_median = np.median(rotation_errors)
    rot_std = np.std(rotation_errors)
    return {'translation': {'rmse': trans_rmse, 'mean': trans_mean, 'median': trans_median, 'std': trans_std, 'errors': translation_errors}, 'rotation': {'rmse': rot_rmse, 'mean': rot_mean, 'median': rot_median, 'std': rot_std, 'errors': rotation_errors}, 'delta': delta, 'unit': unit}, None
def detect_failures(ate_errors, threshold=None):
    if threshold is None:
        threshold = cfg.FAILURE_THRESHOLD
    failures = ate_errors > threshold
    failure_indices = np.where(failures)[0]
    if len(failure_indices) == 0:
        return {'count': 0, 'events': [], 'total_duration': 0, 'failure_rate': 0.0}, None
    failure_events = []
    start_idx = failure_indices[0]
    for i in range(1, len(failure_indices)):
        if failure_indices[i] != failure_indices[i-1] + 1:
            failure_events.append({'start': int(start_idx), 'end': int(failure_indices[i-1]), 'duration': int(failure_indices[i-1] - start_idx + 1)})
            start_idx = failure_indices[i]
    failure_events.append({'start': int(start_idx), 'end': int(failure_indices[-1]), 'duration': int(failure_indices[-1] - start_idx + 1)})
    total_duration = sum(event['duration'] for event in failure_events)
    return {'count': len(failure_events), 'events': failure_events, 'total_duration': total_duration, 'failure_rate': len(failure_indices) / len(ate_errors)}, None
def compute_completion_rate(estimated_poses, ground_truth_poses, threshold=None):
    if threshold is None:
        threshold = cfg.COMPLETION_THRESHOLD
    completion_rate = len(estimated_poses) / len(ground_truth_poses)
    return {'completion_rate': completion_rate, 'completed': completion_rate >= threshold}, None
def compute_robustness_score(ate_metrics, failure_info, completion_info):
    failure_penalty = failure_info['failure_rate'] * 50
    completion_bonus = completion_info['completion_rate'] * 30
    if ate_metrics['rmse'] > 0:
        accuracy_score = max(0, 50 - ate_metrics['rmse'] * 10)
    else:
        accuracy_score = 50
    robustness_score = accuracy_score + completion_bonus - failure_penalty
    robustness_score = np.clip(robustness_score, 0, 100)
    return {'score': robustness_score, 'accuracy_component': accuracy_score, 'completion_component': completion_bonus, 'failure_component': failure_penalty}, None
def evaluate_trajectory(estimated_poses, ground_truth_poses, config=None):
    if config is None:
        config = cfg.METRICS_CONFIG
    results = {}
    if config['ate']['enabled']:
        ate_result, error = compute_ate(estimated_poses, ground_truth_poses)
        if error:
            return None, f'ate_computation_failed_{error}'
        results['ate'] = ate_result
    else:
        results['ate'] = None
    if config['rpe']['enabled']:
        rpe_results = {}
        for delta in config['rpe']['delta']:
            rpe_result, error = compute_rpe(estimated_poses, ground_truth_poses, delta=delta, unit='frames')
            if error:
                return None, f'rpe_computation_failed_{error}'
            rpe_results[f'delta_{int(delta)}'] = rpe_result
        results['rpe'] = rpe_results
    else:
        results['rpe'] = None
    if config['robustness']['enabled'] and results['ate'] is not None:
        failure_info, error = detect_failures(results['ate']['errors'], threshold=config['robustness']['threshold'])
        if error:
            return None, f'failure_detection_failed_{error}'
        results['failures'] = failure_info
        completion_info, error = compute_completion_rate(estimated_poses, ground_truth_poses, threshold=config['completion']['threshold'])
        if error:
            return None, f'completion_computation_failed_{error}'
        results['completion'] = completion_info
        robustness, error = compute_robustness_score(results['ate'], failure_info, completion_info)
        if error:
            return None, f'robustness_computation_failed_{error}'
        results['robustness'] = robustness
    else:
        results['failures'] = None
        results['completion'] = None
        results['robustness'] = None
    return results, None
