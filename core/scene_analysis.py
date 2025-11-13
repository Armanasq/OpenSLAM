import numpy as np
from core.trajectory import extract_positions
def estimate_scene_complexity(poses, timestamps=None):
    positions = extract_positions(poses)
    if positions is None:
        return None, 'invalid_pose_format'
    path_variance = np.var(positions, axis=0)
    path_complexity = np.sum(path_variance)
    direction_changes = 0
    if len(positions) > 2:
        for i in range(1, len(positions) - 1):
            v1 = positions[i] - positions[i-1]
            v2 = positions[i+1] - positions[i]
            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                v1_norm = v1 / np.linalg.norm(v1)
                v2_norm = v2 / np.linalg.norm(v2)
                angle = np.arccos(np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0))
                if angle > np.pi / 4:
                    direction_changes += 1
    turn_density = direction_changes / len(positions) if len(positions) > 0 else 0
    bbox_min = np.min(positions, axis=0)
    bbox_max = np.max(positions, axis=0)
    bbox_volume = np.prod(bbox_max - bbox_min)
    if path_complexity < 10:
        complexity_level = 'low'
    elif path_complexity < 100:
        complexity_level = 'medium'
    else:
        complexity_level = 'high'
    return {'complexity_score': float(path_complexity), 'level': complexity_level, 'direction_changes': direction_changes, 'turn_density': float(turn_density), 'bbox_volume': float(bbox_volume)}, None
def analyze_coverage(poses):
    positions = extract_positions(poses)
    if positions is None:
        return None, 'invalid_pose_format'
    bbox_min = np.min(positions, axis=0)
    bbox_max = np.max(positions, axis=0)
    bbox_size = bbox_max - bbox_min
    grid_size = 1.0
    if np.any(bbox_size == 0):
        return None, 'degenerate_trajectory'
    grid_dims = np.ceil(bbox_size / grid_size).astype(int)
    if np.prod(grid_dims) > 1000000:
        return None, 'grid_too_large'
    visited_cells = set()
    for pos in positions:
        cell = tuple(((pos - bbox_min) / grid_size).astype(int))
        visited_cells.add(cell)
    total_cells = np.prod(grid_dims)
    coverage_ratio = len(visited_cells) / total_cells if total_cells > 0 else 0
    return {'visited_cells': len(visited_cells), 'total_cells': int(total_cells), 'coverage_ratio': float(coverage_ratio), 'bbox_size': bbox_size.tolist()}, None
def detect_loops(poses, threshold=2.0):
    positions = extract_positions(poses)
    if positions is None:
        return None, 'invalid_pose_format'
    loop_closures = []
    for i in range(len(positions)):
        for j in range(i + 20, len(positions)):
            distance = np.linalg.norm(positions[i] - positions[j])
            if distance < threshold:
                loop_closures.append({'start': i, 'end': j, 'distance': float(distance)})
    return {'count': len(loop_closures), 'closures': loop_closures}, None
