import yaml
import re
import numpy as np
from pathlib import Path
import connector_config as ccfg

class ConnectorEngine:
    def __init__(self):
        self.connectors = {}
        self.transforms = {}
        self.parsers = {}
        self.generators = {}
        self._load_builtin()
        self._load_connector_library()

    def _load_builtin(self):
        self.transforms = dict(ccfg.BUILTIN_TRANSFORMS)
        self.parsers = dict(ccfg.BUILTIN_PARSERS)
        self.generators = dict(ccfg.BUILTIN_GENERATORS)

    def _load_connector_library(self):
        connector_dir = Path(ccfg.CONNECTOR_DIR)
        if not connector_dir.exists():
            return
        for connector_file in connector_dir.rglob('*.yaml'):
            self.load_connector(str(connector_file))

    def load_connector(self, path):
        connector_path = Path(path)
        if not connector_path.exists():
            return None, 'connector_file_not_found'
        with open(connector_path, 'r') as f:
            config = yaml.safe_load(f)
        connector_type = config.get('type', 'transform')
        connector_name = config.get('name')
        if not connector_name:
            return None, 'connector_name_missing'
        self.connectors[connector_name] = config
        if connector_type == 'transform':
            self.transforms[connector_name] = config
        elif connector_type == 'parser':
            self.parsers[connector_name] = config
        elif connector_type == 'generator':
            self.generators[connector_name] = config
        return config, None

    def execute_connector(self, connector_name, input_data, params=None):
        if connector_name not in self.connectors:
            return None, 'connector_not_found'
        config = self.connectors[connector_name]
        connector_type = config.get('type', 'transform')
        if connector_type == 'transform':
            return self._execute_transform(config, input_data, params)
        elif connector_type == 'parser':
            return self._execute_parser(config, input_data, params)
        elif connector_type == 'generator':
            return self._execute_generator(config, input_data, params)
        return None, 'unknown_connector_type'

    def _execute_transform(self, config, input_data, params):
        method = config.get('method')
        if method == 'quaternion_to_matrix':
            return self._quaternion_to_matrix(input_data), None
        elif method == 'matrix_to_quaternion':
            return self._matrix_to_quaternion(input_data), None
        elif method == 'mapping':
            return self._apply_mapping(config, input_data, params), None
        elif method == 'template':
            return self._apply_template(config, input_data, params), None
        elif method == 'script':
            return self._execute_script(config, input_data, params)
        return None, 'unknown_transform_method'

    def _execute_parser(self, config, input_data, params):
        format_type = config.get('format')
        if format_type == 'tum':
            return self._parse_tum(input_data), None
        elif format_type == 'kitti':
            return self._parse_kitti(input_data), None
        elif format_type == 'regex':
            return self._parse_regex(config, input_data), None
        return None, 'unknown_parser_format'

    def _execute_generator(self, config, input_data, params):
        generator_type = config.get('generates')
        if generator_type == 'image_list':
            return self._generate_image_list(input_data, params), None
        elif generator_type == 'calibration':
            return self._generate_calibration(input_data, params), None
        return None, 'unknown_generator_type'

    def _quaternion_to_matrix(self, quat):
        if len(quat) != 4:
            return None
        qw, qx, qy, qz = quat
        R = np.array([
            [1-2*(qy*qy+qz*qz), 2*(qx*qy-qw*qz), 2*(qx*qz+qw*qy)],
            [2*(qx*qy+qw*qz), 1-2*(qx*qx+qz*qz), 2*(qy*qz-qw*qx)],
            [2*(qx*qz-qw*qy), 2*(qy*qz+qw*qx), 1-2*(qx*qx+qy*qy)]
        ])
        return R

    def _matrix_to_quaternion(self, R):
        trace = np.trace(R)
        if trace > 0:
            s = np.sqrt(trace + 1.0) * 2
            qw = 0.25 * s
            qx = (R[2,1] - R[1,2]) / s
            qy = (R[0,2] - R[2,0]) / s
            qz = (R[1,0] - R[0,1]) / s
        elif R[0,0] > R[1,1] and R[0,0] > R[2,2]:
            s = np.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2]) * 2
            qw = (R[2,1] - R[1,2]) / s
            qx = 0.25 * s
            qy = (R[0,1] + R[1,0]) / s
            qz = (R[0,2] + R[2,0]) / s
        elif R[1,1] > R[2,2]:
            s = np.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2]) * 2
            qw = (R[0,2] - R[2,0]) / s
            qx = (R[0,1] + R[1,0]) / s
            qy = 0.25 * s
            qz = (R[1,2] + R[2,1]) / s
        else:
            s = np.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1]) * 2
            qw = (R[1,0] - R[0,1]) / s
            qx = (R[0,2] + R[2,0]) / s
            qy = (R[1,2] + R[2,1]) / s
            qz = 0.25 * s
        return np.array([qw, qx, qy, qz])

    def _apply_mapping(self, config, input_data, params):
        mapping = config.get('mapping', {})
        output = {}
        for out_key, in_path in mapping.items():
            value = self._extract_value(input_data, in_path)
            output[out_key] = value
        return output

    def _apply_template(self, config, input_data, params):
        template = config.get('template', '')
        variables = self._merge_data(input_data, params)
        result = template
        for key, value in variables.items():
            result = result.replace('{' + key + '}', str(value))
        return result

    def _execute_script(self, config, input_data, params):
        script_path = config.get('script')
        if not script_path:
            return None, 'script_path_missing'
        script_file = Path(script_path)
        if not script_file.exists():
            return None, 'script_file_not_found'
        import subprocess
        import json
        input_json = json.dumps({'input': input_data, 'params': params})
        result = subprocess.run(['python3', str(script_file)], input=input_json, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None, 'script_execution_failed'
        output = json.loads(result.stdout)
        return output, None

    def _parse_tum(self, file_path):
        poses = []
        timestamps = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                parts = line.strip().split()
                if len(parts) < 8:
                    continue
                timestamp = float(parts[0])
                tx, ty, tz = float(parts[1]), float(parts[2]), float(parts[3])
                qx, qy, qz, qw = float(parts[4]), float(parts[5]), float(parts[6]), float(parts[7])
                R = self._quaternion_to_matrix([qw, qx, qy, qz])
                pose = np.eye(4)
                pose[:3, :3] = R
                pose[:3, 3] = [tx, ty, tz]
                poses.append(pose)
                timestamps.append(timestamp)
        return {'poses': np.array(poses), 'timestamps': np.array(timestamps)}

    def _parse_kitti(self, file_path):
        poses = []
        with open(file_path, 'r') as f:
            for line in f:
                values = [float(x) for x in line.strip().split()]
                if len(values) < 12:
                    continue
                pose = np.eye(4)
                pose[0, :] = values[0:4]
                pose[1, :] = values[4:8]
                pose[2, :] = values[8:12]
                poses.append(pose)
        return {'poses': np.array(poses)}

    def _parse_regex(self, config, file_path):
        pattern = config.get('pattern')
        groups = config.get('groups', {})
        results = []
        with open(file_path, 'r') as f:
            for line in f:
                match = re.match(pattern, line.strip())
                if match:
                    data = {}
                    for key, group_idx in groups.items():
                        if isinstance(group_idx, int):
                            data[key] = match.group(group_idx)
                        elif isinstance(group_idx, list):
                            data[key] = [match.group(i) for i in group_idx]
                    results.append(data)
        return results

    def _generate_image_list(self, directory, params):
        dir_path = Path(directory)
        if not dir_path.exists():
            return None
        extensions = params.get('extensions', ['.png', '.jpg', '.jpeg']) if params else ['.png', '.jpg', '.jpeg']
        images = []
        for ext in extensions:
            images.extend(sorted(dir_path.glob(f'*{ext}')))
        return [str(img) for img in images]

    def _generate_calibration(self, input_data, params):
        template = params.get('template', {}) if params else {}
        output = {}
        for key, value in template.items():
            if isinstance(value, str) and value.startswith('$'):
                path = value[1:]
                output[key] = self._extract_value(input_data, path)
            else:
                output[key] = value
        return output

    def _extract_value(self, data, path):
        parts = path.split('.')
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                idx = int(part)
                current = current[idx]
            else:
                return None
            if current is None:
                return None
        return current

    def _merge_data(self, *data_sources):
        merged = {}
        for data in data_sources:
            if data:
                merged.update(data)
        return merged

    def substitute_variables(self, text, variables):
        result = text
        for key, value in variables.items():
            result = result.replace('${' + key + '}', str(value))
        return result
