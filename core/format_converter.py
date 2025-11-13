import numpy as np
from pathlib import Path
import csv
from core.dataset_loader import quaternion_to_matrix
def matrix_to_quaternion(R):
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
    return qw, qx, qy, qz
def convert_kitti_to_tum(poses, output_path, timestamps=None):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for i, pose in enumerate(poses):
            if timestamps is not None:
                timestamp = timestamps[i]
            else:
                timestamp = i * 0.1
            t = pose[:3, 3]
            R = pose[:3, :3]
            qw, qx, qy, qz = matrix_to_quaternion(R)
            f.write(f'{timestamp:.6f} {t[0]:.6f} {t[1]:.6f} {t[2]:.6f} {qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n')
    return str(output_path), None
def convert_tum_to_kitti(poses, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for pose in poses:
            matrix_3x4 = pose[:3, :].flatten()
            line = ' '.join([f'{v:.6f}' for v in matrix_3x4])
            f.write(line + '\n')
    return str(output_path), None
def convert_to_euroc(poses, timestamps, output_path):
    if timestamps is None:
        return None, 'timestamps_required_for_euroc'
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['#timestamp [ns]', 'p_RS_R_x [m]', 'p_RS_R_y [m]', 'p_RS_R_z [m]', 'q_RS_w []', 'q_RS_x []', 'q_RS_y []', 'q_RS_z []'])
        for i, pose in enumerate(poses):
            timestamp_ns = int(timestamps[i] * 1e9)
            t = pose[:3, 3]
            R = pose[:3, :3]
            qw, qx, qy, qz = matrix_to_quaternion(R)
            writer.writerow([timestamp_ns, t[0], t[1], t[2], qw, qx, qy, qz])
    return str(output_path), None
def convert_format(input_path, output_path, input_format, output_format):
    from core import dataset_loader
    dataset, error = dataset_loader.load_dataset(input_path, input_format)
    if error:
        return None, f'load_failed_{error}'
    if 'sequences' in dataset:
        poses = dataset['sequences'][0]['poses']
        timestamps = dataset['sequences'][0]['timestamps']
    else:
        poses = dataset['poses']
        timestamps = dataset['timestamps']
    if output_format == 'kitti':
        return convert_tum_to_kitti(poses, output_path)
    elif output_format == 'tum':
        return convert_kitti_to_tum(poses, output_path, timestamps)
    elif output_format == 'euroc':
        return convert_to_euroc(poses, timestamps, output_path)
    else:
        return None, 'unsupported_output_format'
