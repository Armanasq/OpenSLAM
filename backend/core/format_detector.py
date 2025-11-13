from pathlib import Path
import config

def detect_format(path):
    path = Path(path)

    if not path.exists():
        return None

    files = {f.name for f in path.rglob('*') if f.is_file()}
    dirs = {d.name for d in path.rglob('*') if d.is_dir()}

    scores = {}

    for fmt, rules in config.DATASET_FORMATS.items():
        score = 0
        required = rules['required']
        optional = rules['optional']

        if fmt == 'rosbag':
            if any(f.endswith('.bag') for f in files):
                score += 100
        else:
            for req in required:
                if req in files or req in dirs:
                    score += 10
                else:
                    score = 0
                    break

            for opt in optional:
                if opt in files or opt in dirs:
                    score += 1

        scores[fmt] = score

    best_fmt = max(scores, key=scores.get)
    return best_fmt if scores[best_fmt] > 0 else 'custom'

def get_dataset_structure(path):
    path = Path(path)

    structure = {'path': str(path), 'files': [], 'dirs': [], 'sensors': [], 'frames': 0, 'duration': 0, 'has_gt': False}

    for item in path.iterdir():
        if item.is_file():
            structure['files'].append(item.name)
        elif item.is_dir():
            structure['dirs'].append(item.name)

    fmt = detect_format(path)
    structure['format'] = fmt

    if 'image' in ' '.join(structure['dirs']).lower() or any('cam' in d for d in structure['dirs']):
        structure['sensors'].append('camera')

    if 'velodyne' in structure['dirs'] or 'lidar' in ' '.join(structure['dirs']).lower():
        structure['sensors'].append('lidar')

    if 'imu' in ' '.join(structure['dirs'] + structure['files']).lower():
        structure['sensors'].append('imu')

    if 'groundtruth' in ' '.join(structure['files']).lower() or 'poses' in structure['dirs']:
        structure['has_gt'] = True

    return structure

def validate_dataset(path, fmt=None):
    path = Path(path)

    if fmt is None:
        fmt = detect_format(path)

    if fmt not in config.DATASET_FORMATS:
        return False, [f'unknown format: {fmt}']

    errors = []
    required = config.DATASET_FORMATS[fmt]['required']

    files = {f.name for f in path.rglob('*') if f.is_file()}
    dirs = {d.name for d in path.rglob('*') if d.is_dir()}

    for req in required:
        if req not in files and req not in dirs:
            if not (fmt == 'rosbag' and any(f.endswith('.bag') for f in files)):
                errors.append(f'missing required: {req}')

    return len(errors) == 0, errors
