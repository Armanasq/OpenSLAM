import sys
import argparse
import numpy as np
from pathlib import Path
import openslam_config as cfg
from core import dataset_loader, trajectory, metrics, visualization, motion_analysis, scene_analysis, export, format_converter, statistical_analysis, task_metrics, batch
def format_number(value, decimals=None):
    if decimals is None:
        decimals = cfg.PRECISION_DECIMALS
    return f'{value:.{decimals}f}'
def print_header(text):
    print(f'\n{"="*70}')
    print(f'{text}')
    print(f'{"="*70}\n')
def print_section(title):
    print(f'\n{title}:')
    print(f'{"-"*len(title)}')
def print_metric(name, value, unit=''):
    formatted_value = format_number(value) if isinstance(value, (float, np.float64, np.float32)) else str(value)
    print(f'  {name}: {formatted_value} {unit}')
def preview_dataset(dataset_path, format_type=None, plot=False, detailed=False):
    print_header(f'Dataset Preview: {dataset_path}')
    dataset, error = dataset_loader.load_dataset(dataset_path, format_type)
    if error:
        print(f'Error loading dataset: {error}')
        return 1
    info = dataset_loader.get_dataset_info(dataset)
    print_section('Basic Information')
    print_metric('Name', info['name'])
    print_metric('Format', info['format'])
    print_metric('Path', info['path'])
    if 'total_frames' in info:
        print_metric('Sequences', info['sequences'])
        print_metric('Total Frames', info['total_frames'])
    elif 'frames' in info:
        print_metric('Frames', info['frames'])
    if 'duration' in info:
        print_metric('Duration', info['duration'], 's')
        print_metric('Frequency', info['frequency'], 'Hz')
    if 'sequences' in dataset:
        poses = dataset['sequences'][0]['poses']
        timestamps = dataset['sequences'][0]['timestamps']
    else:
        poses = dataset['poses']
        timestamps = dataset['timestamps']
    print_section('Trajectory Statistics')
    distances, error = trajectory.compute_distances(poses)
    if not error:
        print_metric('Total Distance', distances[-1], 'm')
        print_metric('Avg Distance per Frame', np.mean(np.diff(distances)), 'm')
    if timestamps is not None:
        velocities, error = trajectory.compute_velocities(poses, timestamps)
        if not error:
            print_metric('Max Velocity', np.max(velocities), 'm/s')
            print_metric('Avg Velocity', np.mean(velocities[velocities > 0]), 'm/s')
        angular_vels, error = trajectory.compute_angular_velocities(poses, timestamps)
        if not error:
            print_metric('Max Angular Velocity', np.max(angular_vels), 'rad/s')
            print_metric('Avg Angular Velocity', np.mean(angular_vels[angular_vels > 0]), 'rad/s')
    positions = trajectory.extract_positions(poses)
    if positions is not None:
        bbox_min = np.min(positions, axis=0)
        bbox_max = np.max(positions, axis=0)
        bbox_size = bbox_max - bbox_min
        print_section('Spatial Extent')
        print_metric('Bounding Box Size', f'[{format_number(bbox_size[0])}, {format_number(bbox_size[1])}, {format_number(bbox_size[2])}]', 'm')
        print_metric('Min Position', f'[{format_number(bbox_min[0])}, {format_number(bbox_min[1])}, {format_number(bbox_min[2])}]', 'm')
        print_metric('Max Position', f'[{format_number(bbox_max[0])}, {format_number(bbox_max[1])}, {format_number(bbox_max[2])}]', 'm')
    if detailed:
        if timestamps is not None:
            print_section('Motion Analysis')
            motion_result, error = motion_analysis.analyze_motion_patterns(poses, timestamps)
            if not error:
                print_metric('Dominant Motion', motion_result['dominant'])
                print('  Motion Distribution:')
                for category, percentage in motion_result['percentages'].items():
                    if percentage > 0:
                        print(f'    {category}: {format_number(percentage, 2)}%')
            dynamics, error = motion_analysis.analyze_dynamics(poses, timestamps)
            if not error:
                print_section('Dynamics')
                print_metric('Avg Velocity', dynamics['velocity']['mean'], 'm/s')
                print_metric('Max Velocity', dynamics['velocity']['max'], 'm/s')
                print_metric('Avg Acceleration', dynamics['acceleration']['mean'], 'm/s^2')
                print_metric('Max Acceleration', dynamics['acceleration']['max'], 'm/s^2')
        path_eff, error = motion_analysis.compute_path_efficiency(poses)
        if not error:
            print_section('Path Efficiency')
            print_metric('Total Path Length', path_eff['total_distance'], 'm')
            print_metric('Straight Line Distance', path_eff['straight_line_distance'], 'm')
            print_metric('Efficiency', path_eff['efficiency'])
        scene_comp, error = scene_analysis.estimate_scene_complexity(poses, timestamps)
        if not error:
            print_section('Scene Complexity')
            print_metric('Complexity Level', scene_comp['level'])
            print_metric('Complexity Score', scene_comp['complexity_score'])
            print_metric('Direction Changes', scene_comp['direction_changes'])
            print_metric('Turn Density', scene_comp['turn_density'], 'turns/frame')
        loops, error = scene_analysis.detect_loops(poses)
        if not error and loops['count'] > 0:
            print_section('Loop Closures')
            print_metric('Detected Loops', loops['count'])
    if plot:
        print_section('Generating Plots')
        output_dir = cfg.PLOT_DIR / 'preview'
        plot_2d_path = output_dir / 'trajectory_2d.png'
        result, error = visualization.plot_trajectory_2d(poses, plot_2d_path)
        if error:
            print(f'  Error generating 2D plot: {error}')
        else:
            print(f'  2D Trajectory: {result}')
        plot_3d_path = output_dir / 'trajectory_3d.png'
        result, error = visualization.plot_trajectory_3d(poses, plot_3d_path)
        if error:
            print(f'  Error generating 3D plot: {error}')
        else:
            print(f'  3D Trajectory: {result}')
    print()
    return 0
def evaluate_trajectory(estimated_path, ground_truth_path, format_type=None, align=True, output_dir=None):
    print_header('Trajectory Evaluation')
    print_section('Loading Data')
    print(f'  Estimated: {estimated_path}')
    est_dataset, error = dataset_loader.load_dataset(estimated_path, format_type)
    if error:
        print(f'Error loading estimated trajectory: {error}')
        return 1
    print(f'  Ground Truth: {ground_truth_path}')
    gt_dataset, error = dataset_loader.load_dataset(ground_truth_path, format_type)
    if error:
        print(f'Error loading ground truth: {error}')
        return 1
    if 'sequences' in est_dataset:
        est_poses = est_dataset['sequences'][0]['poses']
        est_timestamps = est_dataset['sequences'][0]['timestamps']
    else:
        est_poses = est_dataset['poses']
        est_timestamps = est_dataset['timestamps']
    if 'sequences' in gt_dataset:
        gt_poses = gt_dataset['sequences'][0]['poses']
        gt_timestamps = gt_dataset['sequences'][0]['timestamps']
    else:
        gt_poses = gt_dataset['poses']
        gt_timestamps = gt_dataset['timestamps']
    if est_timestamps is not None and gt_timestamps is not None:
        print_section('Synchronizing Trajectories')
        sync_result, error = trajectory.synchronize_trajectories(est_timestamps, est_poses, gt_timestamps, gt_poses)
        if error:
            print(f'Error synchronizing: {error}')
            return 1
        est_poses = sync_result['traj1']['poses']
        gt_poses = sync_result['traj2']['poses']
        print_metric('Synchronized Frames', sync_result['num_matches'])
    if align:
        print_section('Aligning Trajectories')
        align_result, error = trajectory.align_trajectories(est_poses, gt_poses, method=cfg.DEFAULT_ALIGNMENT)
        if error:
            print(f'Error aligning: {error}')
            return 1
        est_poses = align_result['aligned_poses']
        print_metric('Alignment Method', align_result['method'])
    print_section('Computing Metrics')
    eval_results, error = metrics.evaluate_trajectory(est_poses, gt_poses)
    if error:
        print(f'Error computing metrics: {error}')
        return 1
    print_section('ATE Metrics')
    ate = eval_results['ate']
    print_metric('RMSE', ate['rmse'], 'm')
    print_metric('Mean', ate['mean'], 'm')
    print_metric('Median', ate['median'], 'm')
    print_metric('Std Dev', ate['std'], 'm')
    print_metric('Max', ate['max'], 'm')
    print_metric('Min', ate['min'], 'm')
    if eval_results['rpe'] is not None:
        print_section('RPE Metrics')
        for delta_key, rpe in eval_results['rpe'].items():
            print(f'\n  Delta = {rpe["delta"]} {rpe["unit"]}:')
            print_metric('    Translation RMSE', rpe['translation']['rmse'], 'm')
            print_metric('    Translation Mean', rpe['translation']['mean'], 'm')
            print_metric('    Rotation RMSE', rpe['rotation']['rmse'], 'deg')
            print_metric('    Rotation Mean', rpe['rotation']['mean'], 'deg')
    if eval_results['robustness'] is not None:
        print_section('Robustness Analysis')
        print_metric('Robustness Score', eval_results['robustness']['score'])
        print_metric('Completion Rate', eval_results['completion']['completion_rate'])
        print_metric('Failure Count', eval_results['failures']['count'])
        if eval_results['failures']['count'] > 0:
            print_metric('Total Failure Duration', eval_results['failures']['total_duration'], 'frames')
            print_metric('Failure Rate', eval_results['failures']['failure_rate'])
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        print_section('Generating Visualizations')
        traj_2d_path = output_dir / 'trajectory_2d.png'
        result, error = visualization.plot_trajectory_2d(est_poses, traj_2d_path, ground_truth=gt_poses, label='Estimated')
        if not error:
            print(f'  2D Trajectory: {result}')
        traj_3d_path = output_dir / 'trajectory_3d.png'
        result, error = visualization.plot_trajectory_3d(est_poses, traj_3d_path, ground_truth=gt_poses, label='Estimated')
        if not error:
            print(f'  3D Trajectory: {result}')
        error_dist_path = output_dir / 'error_distribution.png'
        result, error = visualization.plot_error_distribution(ate['errors'], error_dist_path, title='ATE Distribution')
        if not error:
            print(f'  Error Distribution: {result}')
        error_frames_path = output_dir / 'error_over_frames.png'
        result, error = visualization.plot_error_over_frames(ate['errors'], error_frames_path, title='ATE Over Frames')
        if not error:
            print(f'  Error Over Frames: {result}')
        error_heatmap_path = output_dir / 'trajectory_error_heatmap.png'
        result, error = visualization.plot_trajectory_with_errors(est_poses, ate['errors'], error_heatmap_path, ground_truth=gt_poses)
        if not error:
            print(f'  Trajectory Error Heatmap: {result}')
        print_section('Exporting Results')
        json_path = output_dir / 'results.json'
        result, error = export.export_to_json(eval_results, json_path)
        if not error:
            print(f'  JSON: {result}')
        csv_path = output_dir / 'results.csv'
        result, error = export.export_to_csv(eval_results, csv_path)
        if not error:
            print(f'  CSV: {result}')
        latex_path = output_dir / 'results.tex'
        result, error = export.export_to_latex(eval_results, latex_path)
        if not error:
            print(f'  LaTeX: {result}')
        hdf5_path = output_dir / 'results.h5'
        result, error = export.export_to_hdf5(eval_results, hdf5_path)
        if not error:
            print(f'  HDF5: {result}')
    print()
    return 0
def convert_format_command(input_path, output_path, input_format, output_format):
    print_header(f'Converting {input_format} to {output_format}')
    result, error = format_converter.convert_format(input_path, output_path, input_format, output_format)
    if error:
        print(f'Error converting: {error}')
        return 1
    print(f'Successfully converted to: {result}')
    return 0
def compare_trajectories(ground_truth_path, estimated_paths, format_type=None, output_dir=None):
    print_header('Multi-Trajectory Comparison')
    print_section('Loading Ground Truth')
    gt_dataset, error = dataset_loader.load_dataset(ground_truth_path, format_type)
    if error:
        print(f'Error loading ground truth: {error}')
        return 1
    if 'sequences' in gt_dataset:
        gt_poses = gt_dataset['sequences'][0]['poses']
        gt_timestamps = gt_dataset['sequences'][0]['timestamps']
    else:
        gt_poses = gt_dataset['poses']
        gt_timestamps = gt_dataset['timestamps']
    print_metric('Ground Truth Frames', len(gt_poses))
    print_section('Evaluating Trajectories')
    all_results = []
    for i, est_path in enumerate(estimated_paths):
        est_path_obj = Path(est_path)
        name = est_path_obj.stem
        print(f'\n  [{i+1}/{len(estimated_paths)}] {name}')
        est_dataset, error = dataset_loader.load_dataset(est_path, format_type)
        if error:
            print(f'    Error: {error}')
            continue
        if 'sequences' in est_dataset:
            est_poses = est_dataset['sequences'][0]['poses']
            est_timestamps = est_dataset['sequences'][0]['timestamps']
        else:
            est_poses = est_dataset['poses']
            est_timestamps = est_dataset['timestamps']
        if est_timestamps is not None and gt_timestamps is not None:
            sync_result, error = trajectory.synchronize_trajectories(est_timestamps, est_poses, gt_timestamps, gt_poses)
            if error:
                print(f'    Sync error: {error}')
                continue
            est_poses = sync_result['traj1']['poses']
            synced_gt_poses = sync_result['traj2']['poses']
        else:
            synced_gt_poses = gt_poses
        align_result, error = trajectory.align_trajectories(est_poses, synced_gt_poses, method=cfg.DEFAULT_ALIGNMENT)
        if error:
            print(f'    Alignment error: {error}')
            continue
        est_poses = align_result['aligned_poses']
        eval_results, error = metrics.evaluate_trajectory(est_poses, synced_gt_poses)
        if error:
            print(f'    Evaluation error: {error}')
            continue
        eval_results['name'] = name
        all_results.append(eval_results)
        print(f'    ATE RMSE: {format_number(eval_results["ate"]["rmse"])} m')
        if eval_results['robustness'] is not None:
            print(f'    Robustness: {format_number(eval_results["robustness"]["score"])}')
    if len(all_results) == 0:
        print('No successful evaluations')
        return 1
    print_section('Comparison Summary')
    best_ate = min(r['ate']['rmse'] for r in all_results)
    best_result = next(r for r in all_results if r['ate']['rmse'] == best_ate)
    print_metric('Best ATE RMSE', best_ate, 'm')
    print_metric('Best Algorithm', best_result['name'])
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        print_section('Generating Comparison Plots')
        comparison_data = [{'name': r['name'], 'value': r['ate']['rmse']} for r in all_results]
        comparison_path = output_dir / 'ate_comparison.png'
        result, error = visualization.plot_comparison(comparison_data, 'ATE RMSE [m]', comparison_path)
        if not error:
            print(f'  ATE Comparison: {result}')
        print_section('Exporting Comparison')
        latex_path = output_dir / 'comparison.tex'
        result, error = export.export_comparison_table(all_results, latex_path)
        if not error:
            print(f'  LaTeX Table: {result}')
        json_path = output_dir / 'comparison.json'
        result, error = export.export_to_json(all_results, json_path)
        if not error:
            print(f'  JSON: {result}')
    print()
    return 0
def analyze_failures_command(result_path, ground_truth_path, format_type=None, output_dir=None):
    print_header('Failure Analysis')
    print_section('Loading Data')
    est_dataset, error = dataset_loader.load_dataset(result_path, format_type)
    if error:
        print(f'Error loading result: {error}')
        return 1
    gt_dataset, error = dataset_loader.load_dataset(ground_truth_path, format_type)
    if error:
        print(f'Error loading ground truth: {error}')
        return 1
    if 'sequences' in est_dataset:
        est_poses = est_dataset['sequences'][0]['poses']
    else:
        est_poses = est_dataset['poses']
    if 'sequences' in gt_dataset:
        gt_poses = gt_dataset['sequences'][0]['poses']
    else:
        gt_poses = gt_dataset['poses']
    align_result, error = trajectory.align_trajectories(est_poses, gt_poses, method=cfg.DEFAULT_ALIGNMENT)
    if error:
        print(f'Error aligning: {error}')
        return 1
    est_poses = align_result['aligned_poses']
    ate_result, error = metrics.compute_ate(est_poses, gt_poses)
    if error:
        print(f'Error computing ATE: {error}')
        return 1
    failure_info, error = metrics.detect_failures(ate_result['errors'])
    if error:
        print(f'Error detecting failures: {error}')
        return 1
    print_section('Failure Detection Results')
    print_metric('Total Failures', failure_info['count'])
    print_metric('Total Duration', failure_info['total_duration'], 'frames')
    print_metric('Failure Rate', failure_info['failure_rate'])
    if failure_info['count'] > 0:
        print_section('Failure Events')
        for i, event in enumerate(failure_info['events'][:10]):
            print(f"  Event {i+1}: frames {event['start']}-{event['end']} (duration: {event['duration']} frames)")
        if len(failure_info['events']) > 10:
            print(f'  ... and {len(failure_info["events"]) - 10} more events')
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        failure_timeline_path = output_dir / 'failure_timeline.png'
        result, error = visualization.plot_error_over_frames(ate_result['errors'], failure_timeline_path, title='Failure Timeline')
        if not error:
            print_section('Visualization')
            print(f'  Failure Timeline: {result}')
    print()
    return 0
def batch_evaluation_command(config_path, parallel=1):
    print_header('Batch Evaluation')
    print_section('Loading Configuration')
    config, error = batch.load_batch_config(config_path)
    if error:
        print(f'Error loading config: {error}')
        return 1
    print_metric('Datasets', len(config['datasets']))
    print_metric('Algorithms', len(config['algorithms']))
    print_metric('Parallel Workers', parallel)
    print_section('Running Evaluations')
    batch_result, error = batch.run_batch_evaluation(config, parallel=parallel)
    if error:
        print(f'Error running batch: {error}')
        return 1
    print_section('Batch Results')
    print_metric('Total Evaluations', batch_result['total_evaluations'])
    print_metric('Successful', batch_result['successful'])
    print_metric('Failed', batch_result['total_evaluations'] - batch_result['successful'])
    if config.get('output'):
        output_dir = Path(config['output']['directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        print_section('Exporting Results')
        results_json = output_dir / 'batch_results.json'
        result, error = export.export_to_json(batch_result, results_json)
        if not error:
            print(f'  Results: {result}')
    print()
    return 0
def main():
    parser = argparse.ArgumentParser(description='OpenSLAM: Research-Grade SLAM Evaluation System', formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    preview_parser = subparsers.add_parser('preview', help='Preview dataset information')
    preview_parser.add_argument('dataset', type=str, help='Path to dataset')
    preview_parser.add_argument('--format', type=str, default=None, help='Dataset format (kitti, tum, euroc)')
    preview_parser.add_argument('--plot', action='store_true', help='Generate trajectory plots')
    preview_parser.add_argument('--detailed', action='store_true', help='Show detailed analysis')
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate trajectory against ground truth')
    eval_parser.add_argument('estimated', type=str, help='Path to estimated trajectory')
    eval_parser.add_argument('ground_truth', type=str, help='Path to ground truth trajectory')
    eval_parser.add_argument('--format', type=str, default=None, help='Dataset format (kitti, tum, euroc)')
    eval_parser.add_argument('--no-align', action='store_true', help='Skip trajectory alignment')
    eval_parser.add_argument('--output', type=str, default=None, help='Output directory for results')
    convert_parser = subparsers.add_parser('convert', help='Convert between dataset formats')
    convert_parser.add_argument('input', type=str, help='Input file path')
    convert_parser.add_argument('output', type=str, help='Output file path')
    convert_parser.add_argument('--input-format', type=str, required=True, help='Input format (kitti, tum, euroc)')
    convert_parser.add_argument('--output-format', type=str, required=True, help='Output format (kitti, tum, euroc)')
    compare_parser = subparsers.add_parser('compare', help='Compare multiple trajectories')
    compare_parser.add_argument('ground_truth', type=str, help='Path to ground truth')
    compare_parser.add_argument('trajectories', nargs='+', help='Paths to estimated trajectories')
    compare_parser.add_argument('--format', type=str, default=None, help='Dataset format (kitti, tum, euroc)')
    compare_parser.add_argument('--output', type=str, default=None, help='Output directory for results')
    analyze_failures_parser = subparsers.add_parser('analyze-failures', help='Analyze failure events in trajectory')
    analyze_failures_parser.add_argument('result', type=str, help='Path to estimated trajectory')
    analyze_failures_parser.add_argument('ground_truth', type=str, help='Path to ground truth')
    analyze_failures_parser.add_argument('--format', type=str, default=None, help='Dataset format (kitti, tum, euroc)')
    analyze_failures_parser.add_argument('--output', type=str, default=None, help='Output directory for visualizations')
    batch_parser = subparsers.add_parser('batch', help='Run batch evaluation from YAML config')
    batch_parser.add_argument('config', type=str, help='Path to YAML configuration file')
    batch_parser.add_argument('--parallel', type=int, default=1, help='Number of parallel workers')
    args = parser.parse_args()
    if args.command == 'preview':
        return preview_dataset(args.dataset, format_type=args.format, plot=args.plot, detailed=args.detailed)
    elif args.command == 'evaluate':
        return evaluate_trajectory(args.estimated, args.ground_truth, format_type=args.format, align=not args.no_align, output_dir=args.output)
    elif args.command == 'convert':
        return convert_format_command(args.input, args.output, args.input_format, args.output_format)
    elif args.command == 'compare':
        return compare_trajectories(args.ground_truth, args.trajectories, format_type=args.format, output_dir=args.output)
    elif args.command == 'analyze-failures':
        return analyze_failures_command(args.result, args.ground_truth, format_type=args.format, output_dir=args.output)
    elif args.command == 'batch':
        return batch_evaluation_command(args.config, parallel=args.parallel)
    else:
        parser.print_help()
        return 1
if __name__ == '__main__':
    sys.exit(main())
