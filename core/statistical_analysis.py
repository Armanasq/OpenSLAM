import numpy as np
from scipy import stats
def wilcoxon_signed_rank_test(results1, results2):
    if len(results1) != len(results2):
        return None, 'length_mismatch'
    if len(results1) < 2:
        return None, 'insufficient_samples'
    errors1 = np.array([r['ate']['rmse'] for r in results1])
    errors2 = np.array([r['ate']['rmse'] for r in results2])
    statistic, pvalue = stats.wilcoxon(errors1, errors2)
    significant = pvalue < 0.05
    effect_size = np.abs(np.mean(errors1) - np.mean(errors2)) / np.std(errors1 - errors2) if np.std(errors1 - errors2) > 0 else 0
    return {'statistic': float(statistic), 'pvalue': float(pvalue), 'significant': significant, 'effect_size': float(effect_size), 'alpha': 0.05}, None
def friedman_test(results_list):
    if len(results_list) < 3:
        return None, 'need_at_least_3_algorithms'
    num_algorithms = len(results_list)
    num_datasets = len(results_list[0])
    for results in results_list:
        if len(results) != num_datasets:
            return None, 'inconsistent_dataset_counts'
    data_matrix = np.zeros((num_datasets, num_algorithms))
    for i, results in enumerate(results_list):
        for j, result in enumerate(results):
            data_matrix[j, i] = result['ate']['rmse']
    statistic, pvalue = stats.friedmanchisquare(*[data_matrix[:, i] for i in range(num_algorithms)])
    significant = pvalue < 0.05
    return {'statistic': float(statistic), 'pvalue': float(pvalue), 'significant': significant, 'num_algorithms': num_algorithms, 'num_datasets': num_datasets, 'alpha': 0.05}, None
def bootstrap_confidence_interval(errors, confidence=0.95, num_iterations=1000):
    if len(errors) < 2:
        return None, 'insufficient_data'
    if not (0 < confidence < 1):
        return None, 'invalid_confidence_level'
    bootstrap_means = np.zeros(num_iterations)
    for i in range(num_iterations):
        sample = np.random.choice(errors, size=len(errors), replace=True)
        bootstrap_means[i] = np.mean(sample)
    alpha = 1 - confidence
    lower_percentile = alpha / 2 * 100
    upper_percentile = (1 - alpha / 2) * 100
    lower_bound = np.percentile(bootstrap_means, lower_percentile)
    upper_bound = np.percentile(bootstrap_means, upper_percentile)
    mean = np.mean(errors)
    return {'mean': float(mean), 'lower_bound': float(lower_bound), 'upper_bound': float(upper_bound), 'confidence': confidence}, None
def compute_effect_size(errors1, errors2):
    if len(errors1) < 2 or len(errors2) < 2:
        return None, 'insufficient_data'
    mean1 = np.mean(errors1)
    mean2 = np.mean(errors2)
    std1 = np.std(errors1, ddof=1)
    std2 = np.std(errors2, ddof=1)
    pooled_std = np.sqrt(((len(errors1) - 1) * std1**2 + (len(errors2) - 1) * std2**2) / (len(errors1) + len(errors2) - 2))
    cohens_d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0
    if abs(cohens_d) < 0.2:
        magnitude = 'negligible'
    elif abs(cohens_d) < 0.5:
        magnitude = 'small'
    elif abs(cohens_d) < 0.8:
        magnitude = 'medium'
    else:
        magnitude = 'large'
    return {'cohens_d': float(cohens_d), 'magnitude': magnitude, 'mean_difference': float(mean1 - mean2)}, None
def ranksum_test(errors1, errors2):
    if len(errors1) < 2 or len(errors2) < 2:
        return None, 'insufficient_data'
    statistic, pvalue = stats.ranksums(errors1, errors2)
    significant = pvalue < 0.05
    return {'statistic': float(statistic), 'pvalue': float(pvalue), 'significant': significant, 'alpha': 0.05}, None
def ttest_independent(results1, results2):
    if len(results1) < 2 or len(results2) < 2:
        return None, 'insufficient_samples'
    errors1 = np.array([r['ate']['rmse'] for r in results1])
    errors2 = np.array([r['ate']['rmse'] for r in results2])
    statistic, pvalue = stats.ttest_ind(errors1, errors2)
    significant = pvalue < 0.05
    mean1 = np.mean(errors1)
    mean2 = np.mean(errors2)
    std1 = np.std(errors1, ddof=1)
    std2 = np.std(errors2, ddof=1)
    pooled_std = np.sqrt(((len(errors1) - 1) * std1**2 + (len(errors2) - 1) * std2**2) / (len(errors1) + len(errors2) - 2))
    cohens_d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0
    return {'statistic': float(statistic), 'pvalue': float(pvalue), 'significant': significant, 'cohens_d': float(cohens_d), 'mean1': float(mean1), 'mean2': float(mean2), 'alpha': 0.05}, None
def ttest_paired(results1, results2):
    if len(results1) != len(results2):
        return None, 'length_mismatch'
    if len(results1) < 2:
        return None, 'insufficient_samples'
    errors1 = np.array([r['ate']['rmse'] for r in results1])
    errors2 = np.array([r['ate']['rmse'] for r in results2])
    statistic, pvalue = stats.ttest_rel(errors1, errors2)
    significant = pvalue < 0.05
    mean_diff = np.mean(errors1 - errors2)
    std_diff = np.std(errors1 - errors2, ddof=1)
    return {'statistic': float(statistic), 'pvalue': float(pvalue), 'significant': significant, 'mean_difference': float(mean_diff), 'std_difference': float(std_diff), 'alpha': 0.05}, None
def compute_multi_run_statistics(results_list):
    if len(results_list) == 0:
        return None, 'empty_results'
    ate_rmses = [r['ate']['rmse'] for r in results_list]
    ate_means = [r['ate']['mean'] for r in results_list]
    ate_stds = [r['ate']['std'] for r in results_list]
    rpe_data = []
    for r in results_list:
        if r.get('rpe') is not None:
            for delta_key, rpe in r['rpe'].items():
                rpe_data.append(rpe['translation']['rmse'])
    robustness_scores = []
    for r in results_list:
        if r.get('robustness') is not None:
            robustness_scores.append(r['robustness']['score'])
    stats_dict = {'ate_rmse_mean': float(np.mean(ate_rmses)), 'ate_rmse_std': float(np.std(ate_rmses, ddof=1)) if len(ate_rmses) > 1 else 0.0, 'ate_rmse_min': float(np.min(ate_rmses)), 'ate_rmse_max': float(np.max(ate_rmses)), 'ate_mean_avg': float(np.mean(ate_means)), 'ate_std_avg': float(np.mean(ate_stds)), 'num_runs': len(results_list)}
    if len(rpe_data) > 0:
        stats_dict['rpe_rmse_mean'] = float(np.mean(rpe_data))
        stats_dict['rpe_rmse_std'] = float(np.std(rpe_data, ddof=1)) if len(rpe_data) > 1 else 0.0
    if len(robustness_scores) > 0:
        stats_dict['robustness_mean'] = float(np.mean(robustness_scores))
        stats_dict['robustness_std'] = float(np.std(robustness_scores, ddof=1)) if len(robustness_scores) > 1 else 0.0
    if len(ate_rmses) > 1:
        cv = np.std(ate_rmses, ddof=1) / np.mean(ate_rmses) if np.mean(ate_rmses) > 0 else 0
        stats_dict['coefficient_of_variation'] = float(cv)
    return stats_dict, None
def anova_test(results_list):
    if len(results_list) < 3:
        return None, 'need_at_least_3_groups'
    groups = []
    for results in results_list:
        errors = [r['ate']['rmse'] for r in results]
        groups.append(errors)
    statistic, pvalue = stats.f_oneway(*groups)
    significant = pvalue < 0.05
    return {'statistic': float(statistic), 'pvalue': float(pvalue), 'significant': significant, 'num_groups': len(groups), 'alpha': 0.05}, None
