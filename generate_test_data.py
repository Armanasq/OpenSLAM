import numpy as np
from pathlib import Path
def generate_circular_trajectory(num_frames=100, radius=10.0, noise_level=0.0):
    angles = np.linspace(0, 2 * np.pi, num_frames)
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    z = np.zeros(num_frames)
    poses = []
    for i in range(num_frames):
        yaw = angles[i] + np.pi / 2
        R = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
        t = np.array([x[i], y[i], z[i]])
        if noise_level > 0:
            t += np.random.normal(0, noise_level, 3)
        pose = np.eye(4)
        pose[:3, :3] = R
        pose[:3, 3] = t
        poses.append(pose)
    return np.array(poses)
def save_kitti_format(poses, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for pose in poses:
            matrix_3x4 = pose[:3, :].flatten()
            line = ' '.join([f'{v:.6f}' for v in matrix_3x4])
            f.write(line + '\n')
def save_tum_format(poses, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for i, pose in enumerate(poses):
            timestamp = i * 0.1
            t = pose[:3, 3]
            R = pose[:3, :3]
            trace = np.trace(R)
            if trace > 0:
                s = 0.5 / np.sqrt(trace + 1.0)
                qw = 0.25 / s
                qx = (R[2,1] - R[1,2]) * s
                qy = (R[0,2] - R[2,0]) * s
                qz = (R[1,0] - R[0,1]) * s
            else:
                if R[0,0] > R[1,1] and R[0,0] > R[2,2]:
                    s = 2.0 * np.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2])
                    qw = (R[2,1] - R[1,2]) / s
                    qx = 0.25 * s
                    qy = (R[0,1] + R[1,0]) / s
                    qz = (R[0,2] + R[2,0]) / s
                elif R[1,1] > R[2,2]:
                    s = 2.0 * np.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2])
                    qw = (R[0,2] - R[2,0]) / s
                    qx = (R[0,1] + R[1,0]) / s
                    qy = 0.25 * s
                    qz = (R[1,2] + R[2,1]) / s
                else:
                    s = 2.0 * np.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1])
                    qw = (R[1,0] - R[0,1]) / s
                    qx = (R[0,2] + R[2,0]) / s
                    qy = (R[1,2] + R[2,1]) / s
                    qz = 0.25 * s
            f.write(f'{timestamp:.6f} {t[0]:.6f} {t[1]:.6f} {t[2]:.6f} {qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n')
data_dir = Path('data/test')
data_dir.mkdir(parents=True, exist_ok=True)
print('generating test trajectories')
gt_trajectory = generate_circular_trajectory(num_frames=200, radius=15.0, noise_level=0.0)
est_trajectory = generate_circular_trajectory(num_frames=200, radius=15.0, noise_level=0.3)
print('saving ground truth (kitti format)')
save_kitti_format(gt_trajectory, data_dir / 'ground_truth_kitti.txt')
print('saving estimated trajectory (kitti format)')
save_kitti_format(est_trajectory, data_dir / 'estimated_kitti.txt')
print('saving ground truth (tum format)')
save_tum_format(gt_trajectory, data_dir / 'ground_truth_tum.txt')
print('saving estimated trajectory (tum format)')
save_tum_format(est_trajectory, data_dir / 'estimated_tum.txt')
print(f'\ntest data generated in {data_dir}')
print(f'  ground truth: {len(gt_trajectory)} frames')
print(f'  estimated: {len(est_trajectory)} frames')
print(f'  trajectory type: circular path radius 15m')
print(f'  noise level: 0.3m')
