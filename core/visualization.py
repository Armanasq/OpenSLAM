import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from config import openslam_config as cfg
from core.trajectory import extract_positions
def setup_plot_style():
    plt.style.use(cfg.PLOT_STYLE)
def plot_trajectory_2d(poses, output_path, ground_truth=None, label='Estimated'):
    positions = extract_positions(poses)
    if positions is None:
        return None, 'invalid_pose_format'
    fig, ax = plt.subplots(figsize=cfg.FIGURE_SIZE_2D, dpi=cfg.PLOT_DPI)
    ax.plot(positions[:, 0], positions[:, 1], 'b-', linewidth=2, label=label, alpha=0.7)
    ax.plot(positions[0, 0], positions[0, 1], 'go', markersize=10, label='Start')
    ax.plot(positions[-1, 0], positions[-1, 1], 'ro', markersize=10, label='End')
    if ground_truth is not None:
        gt_positions = extract_positions(ground_truth)
        if gt_positions is not None:
            ax.plot(gt_positions[:, 0], gt_positions[:, 1], 'k--', linewidth=2, label='Ground Truth', alpha=0.5)
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_title('Trajectory (Top View)')
    ax.legend()
    ax.grid(True)
    ax.axis('equal')
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=cfg.PLOT_DPI)
    plt.close()
    return str(output_path), None
def plot_trajectory_3d(poses, output_path, ground_truth=None, label='Estimated'):
    positions = extract_positions(poses)
    if positions is None:
        return None, 'invalid_pose_format'
    fig = plt.figure(figsize=cfg.FIGURE_SIZE_3D, dpi=cfg.PLOT_DPI)
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(positions[:, 0], positions[:, 1], positions[:, 2], 'b-', linewidth=2, label=label, alpha=0.7)
    ax.plot([positions[0, 0]], [positions[0, 1]], [positions[0, 2]], 'go', markersize=10, label='Start')
    ax.plot([positions[-1, 0]], [positions[-1, 1]], [positions[-1, 2]], 'ro', markersize=10, label='End')
    if ground_truth is not None:
        gt_positions = extract_positions(ground_truth)
        if gt_positions is not None:
            ax.plot(gt_positions[:, 0], gt_positions[:, 1], gt_positions[:, 2], 'k--', linewidth=2, label='Ground Truth', alpha=0.5)
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_zlabel('Z [m]')
    ax.set_title('Trajectory (3D View)')
    ax.legend()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=cfg.PLOT_DPI)
    plt.close()
    return str(output_path), None
def plot_error_distribution(errors, output_path, title='Error Distribution'):
    if len(errors) == 0:
        return None, 'empty_errors'
    fig, ax = plt.subplots(figsize=cfg.FIGURE_SIZE_ERROR, dpi=cfg.PLOT_DPI)
    ax.hist(errors, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    ax.axvline(np.mean(errors), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(errors):.4f}m')
    ax.axvline(np.median(errors), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(errors):.4f}m')
    ax.set_xlabel('Error [m]')
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=cfg.PLOT_DPI)
    plt.close()
    return str(output_path), None
def plot_error_over_frames(errors, output_path, title='Error Over Frames'):
    if len(errors) == 0:
        return None, 'empty_errors'
    fig, ax = plt.subplots(figsize=cfg.FIGURE_SIZE_ERROR, dpi=cfg.PLOT_DPI)
    frames = np.arange(len(errors))
    ax.plot(frames, errors, 'b-', linewidth=1, alpha=0.7)
    ax.axhline(np.mean(errors), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(errors):.4f}m')
    ax.set_xlabel('Frame')
    ax.set_ylabel('Error [m]')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=cfg.PLOT_DPI)
    plt.close()
    return str(output_path), None
def plot_trajectory_with_errors(poses, errors, output_path, ground_truth=None):
    positions = extract_positions(poses)
    if positions is None:
        return None, 'invalid_pose_format'
    if len(positions) != len(errors):
        return None, 'length_mismatch'
    fig, ax = plt.subplots(figsize=cfg.FIGURE_SIZE_2D, dpi=cfg.PLOT_DPI)
    scatter = ax.scatter(positions[:, 0], positions[:, 1], c=errors, cmap='hot', s=20, alpha=0.7, vmin=0, vmax=np.percentile(errors, 95))
    ax.plot(positions[0, 0], positions[0, 1], 'go', markersize=10, label='Start')
    ax.plot(positions[-1, 0], positions[-1, 1], 'ro', markersize=10, label='End')
    if ground_truth is not None:
        gt_positions = extract_positions(ground_truth)
        if gt_positions is not None:
            ax.plot(gt_positions[:, 0], gt_positions[:, 1], 'k--', linewidth=1, label='Ground Truth', alpha=0.3)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Error [m]')
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_title('Trajectory with Error Heatmap')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.axis('equal')
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=cfg.PLOT_DPI)
    plt.close()
    return str(output_path), None
def plot_comparison(results_list, metric_name, output_path):
    if len(results_list) == 0:
        return None, 'empty_results'
    names = [r['name'] for r in results_list]
    values = [r['value'] for r in results_list]
    fig, ax = plt.subplots(figsize=cfg.FIGURE_SIZE_ERROR, dpi=cfg.PLOT_DPI)
    bars = ax.bar(names, values, color='steelblue', edgecolor='black', alpha=0.7)
    for i, (bar, val) in enumerate(zip(bars, values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height, f'{val:.4f}', ha='center', va='bottom')
    ax.set_ylabel(f'{metric_name}')
    ax.set_title(f'{metric_name} Comparison')
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right')
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=cfg.PLOT_DPI)
    plt.close()
    return str(output_path), None
def plot_comparison_box(results_dict, output_path):
    if len(results_dict) == 0:
        return None, 'empty_results'
    labels = list(results_dict.keys())
    data = [results_dict[label] for label in labels]
    fig, ax = plt.subplots(figsize=cfg.FIGURE_SIZE_ERROR, dpi=cfg.PLOT_DPI)
    bp = ax.boxplot(data, labels=labels, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('steelblue')
        patch.set_alpha(0.7)
    for median in bp['medians']:
        median.set_color('red')
        median.set_linewidth(2)
    ax.set_ylabel('Error [m]')
    ax.set_title('Multi-Run Error Distribution')
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right')
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=cfg.PLOT_DPI)
    plt.close()
    return str(output_path), None
def plot_comparison_radar(results_dict, metrics_list, output_path):
    if len(results_dict) == 0:
        return None, 'empty_results'
    if len(metrics_list) < 3:
        return None, 'insufficient_metrics'
    angles = np.linspace(0, 2 * np.pi, len(metrics_list), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(10, 10), dpi=cfg.PLOT_DPI, subplot_kw={'projection': 'polar'})
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink']
    for idx, (label, metrics) in enumerate(results_dict.items()):
        values = []
        for metric_name in metrics_list:
            if metric_name in metrics:
                values.append(metrics[metric_name])
            else:
                values.append(0.0)
        values += values[:1]
        color = colors[idx % len(colors)]
        ax.plot(angles, values, 'o-', linewidth=2, label=label, color=color)
        ax.fill(angles, values, alpha=0.15, color=color)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics_list)
    ax.set_title('Multi-Metric Radar Comparison', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    ax.grid(True)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=cfg.PLOT_DPI)
    plt.close()
    return str(output_path), None
def plot_multi_trajectory_overlay(trajectories_dict, output_path, ground_truth=None, show_3d=False):
    if len(trajectories_dict) == 0:
        return None, 'empty_trajectories'
    if show_3d:
        fig = plt.figure(figsize=cfg.FIGURE_SIZE_3D, dpi=cfg.PLOT_DPI)
        ax = fig.add_subplot(111, projection='3d')
    else:
        fig, ax = plt.subplots(figsize=cfg.FIGURE_SIZE_2D, dpi=cfg.PLOT_DPI)
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan', 'magenta']
    for idx, (label, poses) in enumerate(trajectories_dict.items()):
        positions = extract_positions(poses)
        if positions is None:
            continue
        color = colors[idx % len(colors)]
        if show_3d:
            ax.plot(positions[:, 0], positions[:, 1], positions[:, 2], linewidth=2, label=label, alpha=0.7, color=color)
        else:
            ax.plot(positions[:, 0], positions[:, 1], linewidth=2, label=label, alpha=0.7, color=color)
    if ground_truth is not None:
        gt_positions = extract_positions(ground_truth)
        if gt_positions is not None:
            if show_3d:
                ax.plot(gt_positions[:, 0], gt_positions[:, 1], gt_positions[:, 2], 'k--', linewidth=2, label='Ground Truth', alpha=0.5)
            else:
                ax.plot(gt_positions[:, 0], gt_positions[:, 1], 'k--', linewidth=2, label='Ground Truth', alpha=0.5)
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    if show_3d:
        ax.set_zlabel('Z [m]')
        ax.set_title('Multi-Trajectory Overlay (3D)')
    else:
        ax.set_title('Multi-Trajectory Overlay (2D)')
        ax.axis('equal')
    ax.legend()
    ax.grid(True, alpha=0.3)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=cfg.PLOT_DPI)
    plt.close()
    return str(output_path), None
