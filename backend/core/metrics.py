import numpy as np
from scipy.spatial.transform import Rotation
import config

def compute_ate(estimated, ground_truth):
    n = min(len(estimated), len(ground_truth))

    if len(estimated.shape) == 3:
        est_positions = estimated[:n, :3, 3]
    else:
        est_positions = estimated[:n, :3]

    if len(ground_truth.shape) == 3:
        gt_positions = ground_truth[:n, :3, 3]
    else:
        gt_positions = ground_truth[:n, :3]

    errors = np.linalg.norm(est_positions - gt_positions, axis=1)

    return {'rmse': float(np.sqrt(np.mean(errors ** 2))), 'mean': float(np.mean(errors)), 'median': float(np.median(errors)), 'std': float(np.std(errors)), 'min': float(np.min(errors)), 'max': float(np.max(errors)), 'errors': errors.tolist()}

def compute_rpe(estimated, ground_truth, delta=1):
    n = min(len(estimated), len(ground_truth))

    trans_errors = []
    rot_errors = []

    for i in range(n - delta):
        if len(estimated.shape) == 3:
            est_rel = np.linalg.inv(estimated[i]) @ estimated[i + delta]
            gt_rel = np.linalg.inv(ground_truth[i]) @ ground_truth[i + delta]
        else:
            est_rel = estimated[i + delta] - estimated[i]
            gt_rel = ground_truth[i + delta] - ground_truth[i]
            trans_error = np.linalg.norm(est_rel[:3] - gt_rel[:3])
            trans_errors.append(trans_error)
            continue

        error = np.linalg.inv(gt_rel) @ est_rel

        trans_error = np.linalg.norm(error[:3, 3])
        trans_errors.append(trans_error)

        rot_error = np.arccos(np.clip((np.trace(error[:3, :3]) - 1) / 2, -1, 1))
        rot_errors.append(np.degrees(rot_error))

    trans_errors = np.array(trans_errors)
    rot_errors = np.array(rot_errors) if rot_errors else np.array([0])

    return {'trans_rmse': float(np.sqrt(np.mean(trans_errors ** 2))), 'trans_mean': float(np.mean(trans_errors)), 'trans_median': float(np.median(trans_errors)), 'trans_std': float(np.std(trans_errors)), 'rot_rmse': float(np.sqrt(np.mean(rot_errors ** 2))), 'rot_mean': float(np.mean(rot_errors)), 'rot_median': float(np.median(rot_errors)), 'rot_std': float(np.std(rot_errors)), 'trans_errors': trans_errors.tolist(), 'rot_errors': rot_errors.tolist()}

def compute_all_metrics(estimated, ground_truth, timestamps=None):
    metrics = {}

    metrics['ate'] = compute_ate(estimated, ground_truth)
    metrics['rpe'] = compute_rpe(estimated, ground_truth, delta=1)

    if timestamps is not None and len(timestamps) > 1:
        duration = timestamps[-1] - timestamps[0]
        metrics['duration'] = float(duration)
        metrics['num_frames'] = len(timestamps)
        metrics['avg_fps'] = float(len(timestamps) / duration) if duration > 0 else 0

    metrics['success'] = True
    metrics['completion'] = 1.0

    return metrics

def compute_robustness_score(trajectory, ground_truth, metrics):
    if len(trajectory) == 0:
        return 0.0

    completion = len(trajectory) / len(ground_truth) if len(ground_truth) > 0 else 0

    ate_rmse = metrics.get('ate', {}).get('rmse', float('inf'))
    error_consistency = 1.0 / (1.0 + metrics.get('ate', {}).get('std', 1.0))

    if len(metrics.get('ate', {}).get('errors', [])) > 10:
        errors = np.array(metrics['ate']['errors'])
        failures = np.sum(errors > 1.0)
        failure_rate = failures / len(errors)
        recovery = 1.0 - failure_rate
    else:
        recovery = 1.0

    accuracy_score = np.exp(-ate_rmse) if ate_rmse < float('inf') else 0

    robustness = (completion * 0.3 + error_consistency * 0.2 + recovery * 0.3 + accuracy_score * 0.2) * 100

    return float(np.clip(robustness, 0, 100))

def compute_task_alignment_score(trajectory, ground_truth, task_type='navigation'):
    if task_type not in config.TASK_REQUIREMENTS:
        return 0.0

    requirements = config.TASK_REQUIREMENTS[task_type]

    metrics = compute_all_metrics(trajectory, ground_truth)

    ate_rmse = metrics.get('ate', {}).get('rmse', float('inf'))
    accuracy_score = 1.0 if ate_rmse <= requirements['accuracy'] else requirements['accuracy'] / ate_rmse

    if len(trajectory) >= 10:
        positions = trajectory[:, :3, 3] if len(trajectory.shape) == 3 else trajectory[:, :3]
        repeated = positions[::5]
        if len(repeated) > 1:
            precision = np.std([np.linalg.norm(repeated[i] - repeated[0]) for i in range(len(repeated))])
            precision_score = 1.0 if precision <= requirements['precision'] else requirements['precision'] / precision
        else:
            precision_score = 1.0
    else:
        precision_score = 0.5

    robustness_score = compute_robustness_score(trajectory, ground_truth, metrics) / 100

    update_rate_score = 1.0

    tas = (accuracy_score * 0.3 + precision_score * 0.3 + robustness_score * 0.2 + update_rate_score * 0.2) * 100

    return float(np.clip(tas, 0, 100))

def compute_multi_run_statistics(results_list):
    if not results_list:
        return {}

    ate_rmses = [r.get('ate', {}).get('rmse', 0) for r in results_list]
    rpe_rmses = [r.get('rpe', {}).get('trans_rmse', 0) for r in results_list]

    stats = {'ate_mean': float(np.mean(ate_rmses)), 'ate_std': float(np.std(ate_rmses)), 'ate_min': float(np.min(ate_rmses)), 'ate_max': float(np.max(ate_rmses)), 'rpe_mean': float(np.mean(rpe_rmses)), 'rpe_std': float(np.std(rpe_rmses)), 'num_runs': len(results_list), 'success_rate': float(sum(1 for r in results_list if r.get('success', False)) / len(results_list))}

    return stats

def statistical_comparison(results_a, results_b):
    from scipy import stats as scipy_stats

    ate_a = [r.get('ate', {}).get('rmse', 0) for r in results_a]
    ate_b = [r.get('ate', {}).get('rmse', 0) for r in results_b]

    t_stat, p_value = scipy_stats.ttest_ind(ate_a, ate_b)

    mean_a = np.mean(ate_a)
    mean_b = np.mean(ate_b)
    pooled_std = np.sqrt((np.std(ate_a) ** 2 + np.std(ate_b) ** 2) / 2)
    cohens_d = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0

    return {'t_statistic': float(t_stat), 'p_value': float(p_value), 'cohens_d': float(cohens_d), 'significant': bool(p_value < config.SIGNIFICANCE_LEVEL), 'mean_a': float(mean_a), 'mean_b': float(mean_b), 'interpretation': _interpret_cohens_d(cohens_d)}

def _interpret_cohens_d(d):
    abs_d = abs(d)
    if abs_d < 0.2:
        return 'negligible'
    elif abs_d < 0.5:
        return 'small'
    elif abs_d < 0.8:
        return 'medium'
    else:
        return 'large'
