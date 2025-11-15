import numpy as np
from pathlib import Path
from generate_test_data import generate_circular_trajectory, save_kitti_format
data_dir = Path('data/test')
data_dir.mkdir(parents=True, exist_ok=True)
print('generating multiple algorithm results for comparison')
gt_trajectory = generate_circular_trajectory(num_frames=200, radius=15.0, noise_level=0.0)
save_kitti_format(gt_trajectory, data_dir / 'ground_truth_kitti.txt')
print('ground truth saved')
algo1_trajectory = generate_circular_trajectory(num_frames=200, radius=15.0, noise_level=0.2)
save_kitti_format(algo1_trajectory, data_dir / 'algo1_result.txt')
print('algo1 (noise 0.2m) saved')
algo2_trajectory = generate_circular_trajectory(num_frames=200, radius=15.0, noise_level=0.5)
save_kitti_format(algo2_trajectory, data_dir / 'algo2_result.txt')
print('algo2 (noise 0.5m) saved')
algo3_trajectory = generate_circular_trajectory(num_frames=200, radius=15.0, noise_level=0.8)
save_kitti_format(algo3_trajectory, data_dir / 'algo3_result.txt')
print('algo3 (noise 0.8m) saved')
print('\ntest data ready for comparison')
