import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config

try:
    plt.style.use(config.PLOT_STYLE)
except:
    plt.style.use('default')

def plot_trajectory_2d(trajectories, labels, ground_truth=None, output_path=None):
    fig, ax = plt.subplots(figsize=(10, 10), dpi=config.PLOT_DPI)

    for traj, label in zip(trajectories, labels):
        if len(traj.shape) == 3:
            positions = traj[:, :3, 3]
        else:
            positions = traj[:, :3]

        ax.plot(positions[:, 0], positions[:, 1], label=label, linewidth=2)

    if ground_truth is not None:
        if len(ground_truth.shape) == 3:
            gt_positions = ground_truth[:, :3, 3]
        else:
            gt_positions = ground_truth[:, :3]

        ax.plot(gt_positions[:, 0], gt_positions[:, 1], 'k--', label='Ground Truth', linewidth=2)

    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_title('Trajectory Comparison (Top View)')
    ax.legend()
    ax.grid(True)
    ax.axis('equal')

    if output_path:
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        return str(output_path)
    else:
        return fig

def plot_trajectory_3d(trajectories, labels, ground_truth=None, output_path=None):
    fig = plt.figure(figsize=(12, 10), dpi=config.PLOT_DPI)
    ax = fig.add_subplot(111, projection='3d')

    for traj, label in zip(trajectories, labels):
        if len(traj.shape) == 3:
            positions = traj[:, :3, 3]
        else:
            positions = traj[:, :3]

        ax.plot(positions[:, 0], positions[:, 1], positions[:, 2], label=label, linewidth=2)

    if ground_truth is not None:
        if len(ground_truth.shape) == 3:
            gt_positions = ground_truth[:, :3, 3]
        else:
            gt_positions = ground_truth[:, :3]

        ax.plot(gt_positions[:, 0], gt_positions[:, 1], gt_positions[:, 2], 'k--', label='Ground Truth', linewidth=2)

    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')
    ax.set_title('Trajectory Comparison (3D View)')
    ax.legend()

    if output_path:
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        return str(output_path)
    else:
        return fig

def plot_error_over_time(errors, timestamps=None, output_path=None):
    fig, ax = plt.subplots(figsize=(12, 6), dpi=config.PLOT_DPI)

    x = timestamps if timestamps is not None else range(len(errors))

    ax.plot(x, errors, linewidth=2)
    ax.set_xlabel('Time [s]' if timestamps is not None else 'Frame')
    ax.set_ylabel('Error [m]')
    ax.set_title('Error Over Time')
    ax.grid(True)

    if output_path:
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        return str(output_path)
    else:
        return fig

def plot_error_distribution(errors, output_path=None):
    fig, ax = plt.subplots(figsize=(10, 6), dpi=config.PLOT_DPI)

    ax.hist(errors, bins=50, edgecolor='black', alpha=0.7)
    ax.axvline(np.mean(errors), color='r', linestyle='--', linewidth=2, label=f'Mean: {np.mean(errors):.3f}m')
    ax.axvline(np.median(errors), color='g', linestyle='--', linewidth=2, label=f'Median: {np.median(errors):.3f}m')

    ax.set_xlabel('Error [m]')
    ax.set_ylabel('Frequency')
    ax.set_title('Error Distribution')
    ax.legend()
    ax.grid(True)

    if output_path:
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        return str(output_path)
    else:
        return fig

def plot_comparison_box(results_dict, metric='ate_rmse', output_path=None):
    fig, ax = plt.subplots(figsize=(10, 6), dpi=config.PLOT_DPI)

    labels = list(results_dict.keys())
    data = [results_dict[label][metric] for label in labels]

    ax.boxplot(data, labels=labels)
    ax.set_ylabel('Error [m]')
    ax.set_title(f'{metric.upper()} Comparison')
    ax.grid(True)

    if output_path:
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        return str(output_path)
    else:
        return fig

def plot_comparison_radar(results_dict, metrics=['ate', 'rpe', 'robustness'], output_path=None):
    fig, ax = plt.subplots(figsize=(8, 8), dpi=config.PLOT_DPI, subplot_kw={'projection': 'polar'})

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    for label, result in results_dict.items():
        values = [result.get(m, 0) for m in metrics]
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=label)
        ax.fill(angles, values, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)
    ax.set_title('Multi-Metric Comparison')
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    ax.grid(True)

    if output_path:
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        return str(output_path)
    else:
        return fig

def generate_all_plots(trajectories, labels, ground_truth, metrics, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plots = {}

    plots['trajectory_2d'] = plot_trajectory_2d(trajectories, labels, ground_truth, output_dir / 'trajectory_2d.png')

    plots['trajectory_3d'] = plot_trajectory_3d(trajectories, labels, ground_truth, output_dir / 'trajectory_3d.png')

    if metrics and 'ate' in metrics and 'errors' in metrics['ate']:
        plots['error_time'] = plot_error_over_time(metrics['ate']['errors'], None, output_dir / 'error_time.png')
        plots['error_dist'] = plot_error_distribution(metrics['ate']['errors'], output_dir / 'error_dist.png')

    plots_json = output_dir / 'plots.json'
    with open(plots_json, 'w') as f:
        json.dump(plots, f, indent=2)

    return plots

def create_comparison_plots(results_list, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plots = {}

    trajectories = [r['trajectory'] for r in results_list]
    labels = [r['label'] for r in results_list]
    ground_truth = results_list[0].get('ground_truth')

    plots['trajectory_2d'] = plot_trajectory_2d(trajectories, labels, ground_truth, output_dir / 'comparison_trajectory_2d.png')

    plots['trajectory_3d'] = plot_trajectory_3d(trajectories, labels, ground_truth, output_dir / 'comparison_trajectory_3d.png')

    metrics_dict = {r['label']: r['metrics'] for r in results_list if 'metrics' in r}

    if metrics_dict:
        ate_data = {label: [m['ate']['rmse']] for label, m in metrics_dict.items()}
        plots['ate_box'] = plot_comparison_box(ate_data, 'ate_rmse', output_dir / 'ate_comparison.png')

    plots_json = output_dir / 'comparison_plots.json'
    with open(plots_json, 'w') as f:
        json.dump(plots, f, indent=2)

    return plots

def export_latex_table(results_list, output_path):
    output_path = Path(output_path)

    lines = []
    lines.append('\\begin{table}[h]')
    lines.append('\\centering')
    lines.append('\\begin{tabular}{|l|c|c|c|c|}')
    lines.append('\\hline')
    lines.append('Algorithm & ATE (m) & RPE (m) & Time (s) & Success \\\\')
    lines.append('\\hline')

    for result in results_list:
        label = result.get('label', 'Unknown')
        ate = result.get('metrics', {}).get('ate', {}).get('rmse', 0)
        rpe = result.get('metrics', {}).get('rpe', {}).get('trans_rmse', 0)
        time = result.get('metrics', {}).get('duration', 0)
        success = result.get('metrics', {}).get('success', False)
        lines.append(f'{label} & {ate:.3f} & {rpe:.3f} & {time:.1f} & {success} \\\\')

    lines.append('\\hline')
    lines.append('\\end{tabular}')
    lines.append('\\caption{SLAM Algorithm Comparison Results}')
    lines.append('\\label{tab:slam_results}')
    lines.append('\\end{table}')

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    return str(output_path)
