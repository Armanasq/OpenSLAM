import sys
import argparse
import numpy as np
from pathlib import Path
import openslam_config as cfg
from core import dataset_loader, trajectory, metrics, visualization
def format_number(value, decimals=None):
    if decimals is None:
        decimals = cfg.PRECISION_DECIMALS
    return f'{value:.{decimals}f}'
def print_header(text):
    print(f'\n{"="*60}')
    print(f'{text}')
    print(f'{"="*60}\n')
def print_section(title):
    print(f'\n{title}:')
    print(f'{"-"*len(title)}')
def print_metric(name, value, unit=''):
    formatted_value = format_number(value) if isinstance(value, (float, np.float64, np.float32)) else str(value)
    print(f'  {name}: {formatted_value} {unit}')
def preview_dataset(dataset_path, format_type=None, plot=False):
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
    print()
    return 0
def main():
    parser = argparse.ArgumentParser(description='OpenSLAM: Research-Grade SLAM Evaluation System', formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    preview_parser = subparsers.add_parser('preview', help='Preview dataset information')
    preview_parser.add_argument('dataset', type=str, help='Path to dataset')
    preview_parser.add_argument('--format', type=str, default=None, help='Dataset format (kitti, tum, euroc)')
    preview_parser.add_argument('--plot', action='store_true', help='Generate trajectory plots')
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate trajectory against ground truth')
    eval_parser.add_argument('estimated', type=str, help='Path to estimated trajectory')
    eval_parser.add_argument('ground_truth', type=str, help='Path to ground truth trajectory')
    eval_parser.add_argument('--format', type=str, default=None, help='Dataset format (kitti, tum, euroc)')
    eval_parser.add_argument('--no-align', action='store_true', help='Skip trajectory alignment')
    eval_parser.add_argument('--output', type=str, default=None, help='Output directory for results')
    args = parser.parse_args()
    if args.command == 'preview':
        return preview_dataset(args.dataset, format_type=args.format, plot=args.plot)
    elif args.command == 'evaluate':
        return evaluate_trajectory(args.estimated, args.ground_truth, format_type=args.format, align=not args.no_align, output_dir=args.output)
    else:
        parser.print_help()
        return 1
if __name__ == '__main__':
    sys.exit(main())
