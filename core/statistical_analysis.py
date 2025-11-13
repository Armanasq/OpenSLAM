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
