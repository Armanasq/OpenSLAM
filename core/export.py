import json
import csv
from pathlib import Path
import numpy as np
from config import openslam_config as cfg
import h5py
def export_to_json(results, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    def convert_numpy(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(item) for item in obj]
        return obj
    clean_results = convert_numpy(results)
    with open(output_path, 'w') as f:
        json.dump(clean_results, f, indent=2)
    return str(output_path), None
def export_to_csv(results, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        if 'ate' in results:
            writer.writerow(['ATE Metrics'])
            writer.writerow(['Metric', 'Value', 'Unit'])
            writer.writerow(['RMSE', f"{results['ate']['rmse']:.{cfg.PRECISION_DECIMALS}f}", 'm'])
            writer.writerow(['Mean', f"{results['ate']['mean']:.{cfg.PRECISION_DECIMALS}f}", 'm'])
            writer.writerow(['Median', f"{results['ate']['median']:.{cfg.PRECISION_DECIMALS}f}", 'm'])
            writer.writerow(['Std Dev', f"{results['ate']['std']:.{cfg.PRECISION_DECIMALS}f}", 'm'])
            writer.writerow(['Max', f"{results['ate']['max']:.{cfg.PRECISION_DECIMALS}f}", 'm'])
            writer.writerow(['Min', f"{results['ate']['min']:.{cfg.PRECISION_DECIMALS}f}", 'm'])
            writer.writerow([])
        if 'rpe' in results and results['rpe'] is not None:
            writer.writerow(['RPE Metrics'])
            for delta_key, rpe in results['rpe'].items():
                writer.writerow([f"Delta {rpe['delta']} {rpe['unit']}"])
                writer.writerow(['Translation RMSE', f"{rpe['translation']['rmse']:.{cfg.PRECISION_DECIMALS}f}", 'm'])
                writer.writerow(['Translation Mean', f"{rpe['translation']['mean']:.{cfg.PRECISION_DECIMALS}f}", 'm'])
                writer.writerow(['Rotation RMSE', f"{rpe['rotation']['rmse']:.{cfg.PRECISION_DECIMALS}f}", 'deg'])
                writer.writerow(['Rotation Mean', f"{rpe['rotation']['mean']:.{cfg.PRECISION_DECIMALS}f}", 'deg'])
                writer.writerow([])
        if 'robustness' in results and results['robustness'] is not None:
            writer.writerow(['Robustness'])
            writer.writerow(['Score', f"{results['robustness']['score']:.{cfg.PRECISION_DECIMALS}f}", ''])
            writer.writerow(['Completion Rate', f"{results['completion']['completion_rate']:.{cfg.PRECISION_DECIMALS}f}", ''])
            writer.writerow(['Failure Count', results['failures']['count'], ''])
    return str(output_path), None
def export_to_latex(results, output_path, style='plain'):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if style in ['ieee', 'neurips', 'icra', 'cvpr']:
        lines.append('\\begin{table}[htbp]')
        lines.append('\\centering')
    else:
        lines.append('\\begin{table}[h]')
        lines.append('\\centering')
    lines.append('\\begin{tabular}{|l|r|l|}')
    lines.append('\\hline')
    lines.append('\\textbf{Metric} & \\textbf{Value} & \\textbf{Unit} \\\\')
    lines.append('\\hline')
    if 'ate' in results:
        lines.append('\\multicolumn{3}{|c|}{\\textbf{Absolute Trajectory Error}} \\\\')
        lines.append('\\hline')
        lines.append(f"RMSE & {results['ate']['rmse']:.{cfg.PRECISION_DECIMALS}f} & m \\\\")
        lines.append(f"Mean & {results['ate']['mean']:.{cfg.PRECISION_DECIMALS}f} & m \\\\")
        lines.append(f"Median & {results['ate']['median']:.{cfg.PRECISION_DECIMALS}f} & m \\\\")
        lines.append(f"Std Dev & {results['ate']['std']:.{cfg.PRECISION_DECIMALS}f} & m \\\\")
        lines.append('\\hline')
    if 'rpe' in results and results['rpe'] is not None:
        lines.append('\\multicolumn{3}{|c|}{\\textbf{Relative Pose Error}} \\\\')
        lines.append('\\hline')
        for delta_key, rpe in list(results['rpe'].items())[:1]:
            lines.append(f"Translation RMSE & {rpe['translation']['rmse']:.{cfg.PRECISION_DECIMALS}f} & m \\\\")
            lines.append(f"Rotation RMSE & {rpe['rotation']['rmse']:.{cfg.PRECISION_DECIMALS}f} & deg \\\\")
        lines.append('\\hline')
    if 'robustness' in results and results['robustness'] is not None:
        lines.append('\\multicolumn{3}{|c|}{\\textbf{Robustness}} \\\\')
        lines.append('\\hline')
        lines.append(f"Score & {results['robustness']['score']:.{cfg.PRECISION_DECIMALS}f} & \\\\")
        lines.append(f"Completion & {results['completion']['completion_rate']:.{cfg.PRECISION_DECIMALS}f} & \\\\")
        lines.append('\\hline')
    lines.append('\\end{tabular}')
    lines.append('\\caption{SLAM Evaluation Results}')
    lines.append('\\label{tab:slam_results}')
    lines.append('\\end{table}')
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    return str(output_path), None
def export_comparison_table(results_list, output_path, style='plain'):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append('\\begin{table}[htbp]')
    lines.append('\\centering')
    lines.append('\\begin{tabular}{|l|c|c|c|c|}')
    lines.append('\\hline')
    lines.append('\\textbf{Algorithm} & \\textbf{ATE RMSE} & \\textbf{RPE RMSE} & \\textbf{Robustness} & \\textbf{Completion} \\\\')
    lines.append('\\hline')
    best_ate = min(r['ate']['rmse'] for r in results_list if 'ate' in r)
    best_rpe = min(r['rpe']['delta_1']['translation']['rmse'] for r in results_list if 'rpe' in r and r['rpe'] is not None)
    best_robustness = max(r['robustness']['score'] for r in results_list if 'robustness' in r and r['robustness'] is not None)
    for result in results_list:
        name = result.get('name', 'Unknown')
        ate_val = result['ate']['rmse'] if 'ate' in result else 0
        ate_str = f"\\textbf{{{ate_val:.4f}}}" if ate_val == best_ate else f"{ate_val:.4f}"
        rpe_val = result['rpe']['delta_1']['translation']['rmse'] if 'rpe' in result and result['rpe'] is not None else 0
        rpe_str = f"\\textbf{{{rpe_val:.4f}}}" if rpe_val == best_rpe else f"{rpe_val:.4f}"
        rob_val = result['robustness']['score'] if 'robustness' in result and result['robustness'] is not None else 0
        rob_str = f"\\textbf{{{rob_val:.2f}}}" if rob_val == best_robustness else f"{rob_val:.2f}"
        comp_val = result['completion']['completion_rate'] if 'completion' in result else 0
        lines.append(f"{name} & {ate_str} & {rpe_str} & {rob_str} & {comp_val:.2f} \\\\")
    lines.append('\\hline')
    lines.append('\\end{tabular}')
    lines.append('\\caption{Multi-Algorithm Comparison}')
    lines.append('\\label{tab:comparison}')
    lines.append('\\end{table}')
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    return str(output_path), None
def export_to_hdf5(results, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(output_path, 'w') as f:
        if 'ate' in results:
            ate_group = f.create_group('ate')
            ate_group.create_dataset('rmse', data=results['ate']['rmse'])
            ate_group.create_dataset('mean', data=results['ate']['mean'])
            ate_group.create_dataset('median', data=results['ate']['median'])
            ate_group.create_dataset('std', data=results['ate']['std'])
            ate_group.create_dataset('max', data=results['ate']['max'])
            ate_group.create_dataset('min', data=results['ate']['min'])
            ate_group.create_dataset('errors', data=results['ate']['errors'])
        if 'rpe' in results and results['rpe'] is not None:
            rpe_group = f.create_group('rpe')
            for delta_key, rpe in results['rpe'].items():
                delta_group = rpe_group.create_group(delta_key)
                delta_group.create_dataset('delta', data=rpe['delta'])
                delta_group.attrs['unit'] = rpe['unit']
                trans_group = delta_group.create_group('translation')
                trans_group.create_dataset('rmse', data=rpe['translation']['rmse'])
                trans_group.create_dataset('mean', data=rpe['translation']['mean'])
                trans_group.create_dataset('median', data=rpe['translation']['median'])
                trans_group.create_dataset('std', data=rpe['translation']['std'])
                trans_group.create_dataset('errors', data=rpe['translation']['errors'])
                rot_group = delta_group.create_group('rotation')
                rot_group.create_dataset('rmse', data=rpe['rotation']['rmse'])
                rot_group.create_dataset('mean', data=rpe['rotation']['mean'])
                rot_group.create_dataset('median', data=rpe['rotation']['median'])
                rot_group.create_dataset('std', data=rpe['rotation']['std'])
                rot_group.create_dataset('errors', data=rpe['rotation']['errors'])
        if 'robustness' in results and results['robustness'] is not None:
            rob_group = f.create_group('robustness')
            rob_group.create_dataset('score', data=results['robustness']['score'])
            if 'completion' in results:
                rob_group.create_dataset('completion_rate', data=results['completion']['completion_rate'])
            if 'failures' in results:
                rob_group.create_dataset('failure_count', data=results['failures']['count'])
                rob_group.create_dataset('failure_rate', data=results['failures']['failure_rate'])
    return str(output_path), None
