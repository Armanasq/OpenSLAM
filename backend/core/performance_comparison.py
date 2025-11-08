import sys
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Any
import io
import base64
from datetime import datetime
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from shared.models import PerformanceMetrics, TrajectoryPoint
from backend.core.performance_analyzer import TrajectoryErrorComputer, ErrorPlotGenerator
class AlgorithmComparison:
    def __init__(self):
        self.algorithm_results = {}
        self.comparison_history = []
    def add_algorithm_result(self, algorithm_id: str, algorithm_name: str, trajectory: List[TrajectoryPoint], metrics: PerformanceMetrics, metadata: Dict = None):
        self.algorithm_results[algorithm_id] = {'name': algorithm_name, 'trajectory': trajectory, 'metrics': metrics, 'metadata': metadata or {}, 'timestamp': datetime.now()}
    def compare_algorithms(self, algorithm_ids: List[str], ground_truth: List[TrajectoryPoint]) -> Dict:
        if not algorithm_ids or len(algorithm_ids) < 2:
            return {'error': 'At least 2 algorithms required for comparison'}
        comparison_data = {'algorithms': {}, 'rankings': {}, 'summary': {}}
        valid_algorithms = []
        for alg_id in algorithm_ids:
            if alg_id in self.algorithm_results:
                valid_algorithms.append(alg_id)
                result = self.algorithm_results[alg_id]
                comparison_data['algorithms'][alg_id] = {'name': result['name'], 'metrics': {'ate': result['metrics'].ate, 'rpe_trans': result['metrics'].rpe_trans, 'rpe_rot': result['metrics'].rpe_rot, 'execution_time': result['metrics'].execution_time, 'memory_usage': result['metrics'].memory_usage}, 'metadata': result['metadata']}
        if len(valid_algorithms) < 2:
            return {'error': 'Not enough valid algorithms for comparison'}
        comparison_data['rankings'] = self._compute_rankings(valid_algorithms)
        comparison_data['summary'] = self._generate_comparison_summary(valid_algorithms)
        comparison_result = {'comparison_id': f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 'algorithms': algorithm_ids, 'data': comparison_data, 'timestamp': datetime.now()}
        self.comparison_history.append(comparison_result)
        return comparison_data
    def _compute_rankings(self, algorithm_ids: List[str]) -> Dict:
        metrics_names = ['ate', 'rpe_trans', 'rpe_rot', 'execution_time', 'memory_usage']
        rankings = {}
        for metric in metrics_names:
            metric_values = []
            for alg_id in algorithm_ids:
                result = self.algorithm_results[alg_id]
                value = getattr(result['metrics'], metric)
                metric_values.append((alg_id, value))
            if metric in ['execution_time', 'memory_usage']:
                sorted_values = sorted(metric_values, key=lambda x: x[1])
            else:
                sorted_values = sorted(metric_values, key=lambda x: x[1])
            rankings[metric] = [{'algorithm_id': alg_id, 'value': value, 'rank': idx + 1} for idx, (alg_id, value) in enumerate(sorted_values)]
        overall_scores = {}
        for alg_id in algorithm_ids:
            score = 0
            for metric in metrics_names:
                rank = next(r['rank'] for r in rankings[metric] if r['algorithm_id'] == alg_id)
                score += rank
            overall_scores[alg_id] = score
        sorted_overall = sorted(overall_scores.items(), key=lambda x: x[1])
        rankings['overall'] = [{'algorithm_id': alg_id, 'score': score, 'rank': idx + 1} for idx, (alg_id, score) in enumerate(sorted_overall)]
        return rankings
    def _generate_comparison_summary(self, algorithm_ids: List[str]) -> Dict:
        summary = {'best_ate': None, 'best_rpe_trans': None, 'best_rpe_rot': None, 'fastest': None, 'most_memory_efficient': None, 'statistics': {}}
        best_ate = min(algorithm_ids, key=lambda x: self.algorithm_results[x]['metrics'].ate)
        best_rpe_trans = min(algorithm_ids, key=lambda x: self.algorithm_results[x]['metrics'].rpe_trans)
        best_rpe_rot = min(algorithm_ids, key=lambda x: self.algorithm_results[x]['metrics'].rpe_rot)
        fastest = min(algorithm_ids, key=lambda x: self.algorithm_results[x]['metrics'].execution_time)
        most_efficient = min(algorithm_ids, key=lambda x: self.algorithm_results[x]['metrics'].memory_usage)
        summary['best_ate'] = {'algorithm_id': best_ate, 'value': self.algorithm_results[best_ate]['metrics'].ate}
        summary['best_rpe_trans'] = {'algorithm_id': best_rpe_trans, 'value': self.algorithm_results[best_rpe_trans]['metrics'].rpe_trans}
        summary['best_rpe_rot'] = {'algorithm_id': best_rpe_rot, 'value': self.algorithm_results[best_rpe_rot]['metrics'].rpe_rot}
        summary['fastest'] = {'algorithm_id': fastest, 'value': self.algorithm_results[fastest]['metrics'].execution_time}
        summary['most_memory_efficient'] = {'algorithm_id': most_efficient, 'value': self.algorithm_results[most_efficient]['metrics'].memory_usage}
        for metric in ['ate', 'rpe_trans', 'rpe_rot', 'execution_time', 'memory_usage']:
            values = [getattr(self.algorithm_results[alg_id]['metrics'], metric) for alg_id in algorithm_ids]
            summary['statistics'][metric] = {'mean': np.mean(values), 'std': np.std(values), 'min': np.min(values), 'max': np.max(values)}
        return summary
    def generate_comparison_plots(self, algorithm_ids: List[str]) -> Dict[str, str]:
        plots = {}
        plots['metrics_comparison'] = self._generate_metrics_comparison_plot(algorithm_ids)
        plots['trajectory_comparison'] = self._generate_trajectory_comparison_plot(algorithm_ids)
        plots['performance_radar'] = self._generate_performance_radar_plot(algorithm_ids)
        return plots
    def _generate_metrics_comparison_plot(self, algorithm_ids: List[str]) -> str:
        metrics = ['ate', 'rpe_trans', 'rpe_rot', 'execution_time', 'memory_usage']
        metric_labels = ['ATE (m)', 'RPE Trans (m)', 'RPE Rot (rad)', 'Exec Time (s)', 'Memory (MB)']
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        for i, (metric, label) in enumerate(zip(metrics, metric_labels)):
            if i >= len(axes):
                break
            ax = axes[i]
            algorithm_names = []
            values = []
            colors = plt.cm.Set3(np.linspace(0, 1, len(algorithm_ids)))
            for j, alg_id in enumerate(algorithm_ids):
                if alg_id in self.algorithm_results:
                    result = self.algorithm_results[alg_id]
                    algorithm_names.append(result['name'][:10])
                    values.append(getattr(result['metrics'], metric))
            bars = ax.bar(algorithm_names, values, color=colors[:len(values)])
            ax.set_title(label)
            ax.set_ylabel('Value')
            ax.tick_params(axis='x', rotation=45)
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height, f'{value:.3f}', ha='center', va='bottom', fontsize=8)
        if len(metrics) < len(axes):
            for i in range(len(metrics), len(axes)):
                fig.delaxes(axes[i])
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        return plot_data
    def _generate_trajectory_comparison_plot(self, algorithm_ids: List[str]) -> str:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        colors = plt.cm.Set3(np.linspace(0, 1, len(algorithm_ids)))
        for i, alg_id in enumerate(algorithm_ids):
            if alg_id in self.algorithm_results:
                result = self.algorithm_results[alg_id]
                trajectory = result['trajectory']
                positions = np.array([point.position for point in trajectory])
                ax1.plot(positions[:, 0], positions[:, 1], color=colors[i], linewidth=2, label=result['name'][:15], alpha=0.8)
                ax2.plot(positions[:, 0], positions[:, 2], color=colors[i], linewidth=2, label=result['name'][:15], alpha=0.8)
        ax1.set_xlabel('X (m)')
        ax1.set_ylabel('Y (m)')
        ax1.set_title('Trajectory Comparison - Top View (X-Y)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.axis('equal')
        ax2.set_xlabel('X (m)')
        ax2.set_ylabel('Z (m)')
        ax2.set_title('Trajectory Comparison - Side View (X-Z)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.axis('equal')
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        return plot_data
    def _generate_performance_radar_plot(self, algorithm_ids: List[str]) -> str:
        metrics = ['ate', 'rpe_trans', 'rpe_rot', 'execution_time', 'memory_usage']
        metric_labels = ['ATE', 'RPE Trans', 'RPE Rot', 'Exec Time', 'Memory']
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]
        colors = plt.cm.Set3(np.linspace(0, 1, len(algorithm_ids)))
        all_values = {metric: [] for metric in metrics}
        for alg_id in algorithm_ids:
            if alg_id in self.algorithm_results:
                result = self.algorithm_results[alg_id]
                for metric in metrics:
                    all_values[metric].append(getattr(result['metrics'], metric))
        normalized_ranges = {}
        for metric in metrics:
            if all_values[metric]:
                min_val = min(all_values[metric])
                max_val = max(all_values[metric])
                normalized_ranges[metric] = (min_val, max_val)
            else:
                normalized_ranges[metric] = (0, 1)
        for i, alg_id in enumerate(algorithm_ids):
            if alg_id in self.algorithm_results:
                result = self.algorithm_results[alg_id]
                values = []
                for metric in metrics:
                    value = getattr(result['metrics'], metric)
                    min_val, max_val = normalized_ranges[metric]
                    if max_val > min_val:
                        normalized = 1 - (value - min_val) / (max_val - min_val)
                    else:
                        normalized = 0.5
                    values.append(normalized)
                values += values[:1]
                ax.plot(angles, values, 'o-', linewidth=2, label=result['name'][:15], color=colors[i])
                ax.fill(angles, values, alpha=0.25, color=colors[i])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels)
        ax.set_ylim(0, 1)
        ax.set_title('Performance Radar Chart\n(Higher values = Better performance)', size=14, pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        ax.grid(True)
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        return plot_data
    def export_comparison_report(self, comparison_data: Dict, format: str = 'json') -> str:
        if format == 'json':
            import json
            return json.dumps(comparison_data, indent=2, default=str)
        elif format == 'csv':
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Algorithm', 'ATE', 'RPE_Trans', 'RPE_Rot', 'Execution_Time', 'Memory_Usage'])
            for alg_id, data in comparison_data['algorithms'].items():
                metrics = data['metrics']
                writer.writerow([data['name'], metrics['ate'], metrics['rpe_trans'], metrics['rpe_rot'], metrics['execution_time'], metrics['memory_usage']])
            return output.getvalue()
        else:
            return str(comparison_data)
    def get_comparison_history(self) -> List[Dict]:
        return self.comparison_history.copy()
    def clear_results(self):
        self.algorithm_results = {}
        self.comparison_history = []
class MetricDefinitions:
    @staticmethod
    def get_metric_definitions() -> Dict[str, Dict]:
        return {'ate': {'name': 'Absolute Trajectory Error', 'description': 'Root mean square error between estimated and ground truth trajectory after optimal alignment', 'unit': 'meters', 'lower_is_better': True, 'formula': 'sqrt(mean((p_est - p_gt)^2))'}, 'rpe_trans': {'name': 'Relative Pose Error (Translation)', 'description': 'Root mean square error of relative translation between consecutive poses', 'unit': 'meters', 'lower_is_better': True, 'formula': 'sqrt(mean(||t_rel_est - t_rel_gt||^2))'}, 'rpe_rot': {'name': 'Relative Pose Error (Rotation)', 'description': 'Root mean square error of relative rotation between consecutive poses', 'unit': 'radians', 'lower_is_better': True, 'formula': 'sqrt(mean(angle(R_rel_est * R_rel_gt^T)^2))'}, 'execution_time': {'name': 'Execution Time', 'description': 'Total time taken to process the entire dataset', 'unit': 'seconds', 'lower_is_better': True, 'formula': 'end_time - start_time'}, 'memory_usage': {'name': 'Memory Usage', 'description': 'Peak memory consumption during algorithm execution', 'unit': 'megabytes', 'lower_is_better': True, 'formula': 'max(memory_samples)'}}
    @staticmethod
    def get_evaluation_guidelines() -> Dict[str, str]:
        return {'ate_excellent': 'ATE < 0.1m - Excellent accuracy for most applications', 'ate_good': '0.1m ≤ ATE < 0.5m - Good accuracy for navigation', 'ate_acceptable': '0.5m ≤ ATE < 1.0m - Acceptable for rough positioning', 'ate_poor': 'ATE ≥ 1.0m - Poor accuracy, needs improvement', 'rpe_excellent': 'RPE < 0.01m/frame - Excellent local consistency', 'rpe_good': '0.01m ≤ RPE < 0.05m/frame - Good local tracking', 'rpe_acceptable': '0.05m ≤ RPE < 0.1m/frame - Acceptable drift rate', 'rpe_poor': 'RPE ≥ 0.1m/frame - High drift, tracking issues', 'time_realtime': 'Exec time < frame_interval - Real-time capable', 'time_nearrealtime': 'Exec time < 2*frame_interval - Near real-time', 'time_offline': 'Exec time > 2*frame_interval - Offline processing only'}