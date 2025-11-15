import yaml
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from config import openslam_config as cfg
from core import dataset_loader, trajectory, metrics
def load_batch_config(config_path):
    config_path = Path(config_path)
    if not config_path.exists():
        return None, 'config_file_not_found'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    if 'datasets' not in config:
        return None, 'missing_datasets_section'
    if 'algorithms' not in config:
        return None, 'missing_algorithms_section'
    return config, None
def evaluate_single_pair(dataset_info, algorithm_info, align=True):
    dataset_path = dataset_info['path']
    dataset_format = dataset_info.get('format')
    algorithm_path = algorithm_info['results']
    algorithm_name = algorithm_info['name']
    gt_dataset, error = dataset_loader.load_dataset(dataset_path, dataset_format)
    if error:
        return {'name': algorithm_name, 'dataset': dataset_path, 'error': f'load_gt_failed_{error}'}, None
    est_dataset, error = dataset_loader.load_dataset(algorithm_path, dataset_format)
    if error:
        return {'name': algorithm_name, 'dataset': dataset_path, 'error': f'load_est_failed_{error}'}, None
    if 'sequences' in gt_dataset:
        gt_poses = gt_dataset['sequences'][0]['poses']
        gt_timestamps = gt_dataset['sequences'][0]['timestamps']
    else:
        gt_poses = gt_dataset['poses']
        gt_timestamps = gt_dataset['timestamps']
    if 'sequences' in est_dataset:
        est_poses = est_dataset['sequences'][0]['poses']
        est_timestamps = est_dataset['sequences'][0]['timestamps']
    else:
        est_poses = est_dataset['poses']
        est_timestamps = est_dataset['timestamps']
    if est_timestamps is not None and gt_timestamps is not None:
        sync_result, error = trajectory.synchronize_trajectories(est_timestamps, est_poses, gt_timestamps, gt_poses)
        if error:
            return {'name': algorithm_name, 'dataset': dataset_path, 'error': f'sync_failed_{error}'}, None
        est_poses = sync_result['traj1']['poses']
        gt_poses = sync_result['traj2']['poses']
    if align:
        align_result, error = trajectory.align_trajectories(est_poses, gt_poses, method=cfg.DEFAULT_ALIGNMENT)
        if error:
            return {'name': algorithm_name, 'dataset': dataset_path, 'error': f'alignment_failed_{error}'}, None
        est_poses = align_result['aligned_poses']
    eval_results, error = metrics.evaluate_trajectory(est_poses, gt_poses)
    if error:
        return {'name': algorithm_name, 'dataset': dataset_path, 'error': f'evaluation_failed_{error}'}, None
    eval_results['name'] = algorithm_name
    eval_results['dataset'] = dataset_path
    return eval_results, None
def run_batch_evaluation(config, parallel=1):
    datasets = config['datasets']
    algorithms = config['algorithms']
    evaluation_pairs = []
    for dataset in datasets:
        for algorithm in algorithms:
            algorithm_path = algorithm['results'].replace('{dataset}', Path(dataset['path']).stem)
            algorithm_info = {'name': algorithm['name'], 'results': algorithm_path}
            evaluation_pairs.append((dataset, algorithm_info))
    results = []
    if parallel <= 1:
        for dataset_info, algorithm_info in evaluation_pairs:
            result, error = evaluate_single_pair(dataset_info, algorithm_info, align=True)
            if error:
                results.append(result)
            else:
                results.append(result)
    else:
        with ProcessPoolExecutor(max_workers=parallel) as executor:
            futures = {executor.submit(evaluate_single_pair, dataset_info, algorithm_info, True): (dataset_info, algorithm_info) for dataset_info, algorithm_info in evaluation_pairs}
            for future in as_completed(futures):
                result, error = future.result()
                results.append(result)
    return {'results': results, 'total_evaluations': len(evaluation_pairs), 'successful': sum(1 for r in results if 'error' not in r)}, None
