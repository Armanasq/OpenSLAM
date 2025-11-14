import numpy as np
import openslam_config as cfg
TASK_REQUIREMENTS = {'navigation': {'ate_threshold': 0.1, 'rpe_threshold': 0.05, 'update_rate': 10, 'robustness_threshold': 0.95}, 'manipulation': {'ate_threshold': 0.05, 'rpe_threshold': 0.02, 'update_rate': 30, 'robustness_threshold': 0.98}, 'inspection': {'ate_threshold': 0.02, 'rpe_threshold': 0.01, 'update_rate': 5, 'robustness_threshold': 0.90}, 'mapping': {'ate_threshold': 0.15, 'rpe_threshold': 0.08, 'update_rate': 5, 'robustness_threshold': 0.85}}
def evaluate_task_alignment(metrics, task_type):
    if task_type not in TASK_REQUIREMENTS:
        return None, 'unknown_task_type'
    requirements = TASK_REQUIREMENTS[task_type]
    ate_pass = metrics['ate']['rmse'] <= requirements['ate_threshold']
    rpe_pass = True
    if metrics['rpe'] is not None:
        rpe_rmse = metrics['rpe']['delta_1']['translation']['rmse']
        rpe_pass = rpe_rmse <= requirements['rpe_threshold']
    robustness_pass = True
    if metrics['completion'] is not None:
        robustness_pass = metrics['completion']['completion_rate'] >= requirements['robustness_threshold']
    passes = sum([ate_pass, rpe_pass, robustness_pass])
    alignment_score = (passes / 3) * 100
    suitable = passes >= 2
    return {'task_type': task_type, 'alignment_score': alignment_score, 'suitable': suitable, 'ate_pass': ate_pass, 'rpe_pass': rpe_pass, 'robustness_pass': robustness_pass, 'requirements': requirements}, None
def compute_accuracy_precision_tradeoff(metrics):
    ate_mean = metrics['ate']['mean']
    ate_std = metrics['ate']['std']
    accuracy_score = 1.0 / (1.0 + ate_mean) if ate_mean >= 0 else 0
    precision_score = 1.0 / (1.0 + ate_std) if ate_std >= 0 else 0
    combined_score = (accuracy_score + precision_score) / 2
    if ate_mean < ate_std:
        bias_type = 'high_precision_low_accuracy'
    elif ate_mean > ate_std * 2:
        bias_type = 'low_precision_high_bias'
    else:
        bias_type = 'balanced'
    return {'accuracy_score': float(accuracy_score), 'precision_score': float(precision_score), 'combined_score': float(combined_score), 'bias_type': bias_type, 'mean_error': float(ate_mean), 'std_error': float(ate_std)}, None
def compute_consistency_metrics(multiple_run_results):
    if len(multiple_run_results) < 2:
        return None, 'need_multiple_runs'
    ate_values = [r['ate']['rmse'] for r in multiple_run_results]
    rpe_values = [r['rpe']['delta_1']['translation']['rmse'] for r in multiple_run_results if r['rpe'] is not None]
    ate_mean = np.mean(ate_values)
    ate_std = np.std(ate_values)
    ate_cv = ate_std / ate_mean if ate_mean > 0 else 0
    consistency_score = max(0, 100 * (1 - ate_cv))
    if ate_cv < 0.1:
        consistency_level = 'high'
    elif ate_cv < 0.3:
        consistency_level = 'medium'
    else:
        consistency_level = 'low'
    return {'ate_mean': float(ate_mean), 'ate_std': float(ate_std), 'ate_coefficient_of_variation': float(ate_cv), 'consistency_score': float(consistency_score), 'consistency_level': consistency_level, 'num_runs': len(multiple_run_results)}, None
def compute_drift_rate(ate_errors, distances):
    if len(ate_errors) != len(distances):
        return None, 'length_mismatch'
    if len(ate_errors) < 2:
        return None, 'insufficient_data'
    drift_per_meter = ate_errors / (distances + 1e-6)
    mean_drift_rate = np.mean(drift_per_meter)
    max_drift_rate = np.max(drift_per_meter)
    return {'mean_drift_rate': float(mean_drift_rate), 'max_drift_rate': float(max_drift_rate), 'unit': 'm_error_per_m_traveled'}, None
