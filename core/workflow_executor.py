import yaml
import tempfile
import shutil
from pathlib import Path
import numpy as np
from core.connector_engine import ConnectorEngine
from core.docker_orchestrator import DockerOrchestrator

class WorkflowExecutor:
    def __init__(self):
        self.connector_engine = ConnectorEngine()
        self.docker_orchestrator = DockerOrchestrator()
        self.temp_dir = None
        self.output_dir = None
        self.variables = {}

    def execute_workflow(self, plugin_config, dataset_path, output_path):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = Path(output_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.variables = {'TEMP_DIR': str(self.temp_dir), 'OUTPUT_DIR': str(self.output_dir), 'DATASET_PATH': dataset_path}

        workflow = plugin_config.get('workflow', {})
        if not workflow:
            workflow = self._create_default_workflow(plugin_config)

        stages = workflow.get('stages', [])
        results = {}

        for stage in stages:
            stage_name = stage.get('name')
            result, error = self._execute_stage(stage, plugin_config, results)
            if error:
                self._cleanup()
                return None, f'stage_{stage_name}_failed: {error}'
            results[stage_name] = result

        trajectory = results.get('extract', {}).get('trajectory')
        if trajectory is None:
            self._cleanup()
            return None, 'no_trajectory_extracted'

        final_result = {'trajectory': trajectory, 'metadata': results}
        return final_result, None

    def _execute_stage(self, stage, plugin_config, previous_results):
        stage_type = stage.get('type')

        if stage_type == 'prepare':
            return self._execute_prepare_stage(stage, plugin_config, previous_results)
        elif stage_type == 'execute':
            return self._execute_docker_stage(stage, plugin_config, previous_results)
        elif stage_type == 'extract':
            return self._execute_extract_stage(stage, plugin_config, previous_results)

        return None, 'unknown_stage_type'

    def _execute_prepare_stage(self, stage, plugin_config, previous_results):
        tasks = stage.get('tasks', [])
        outputs = {}

        for task in tasks:
            task_name = task.get('name')
            connector_name = task.get('connector')
            config = task.get('config', {})

            config_resolved = self._resolve_variables(config)
            input_data = config_resolved.get('input')

            result, error = self.connector_engine.execute_connector(connector_name, input_data, config_resolved)
            if error:
                return None, f'task_{task_name}_failed: {error}'

            output_key = task.get('output')
            if output_key:
                outputs[output_key] = result
                self.variables[output_key] = result

        return outputs, None

    def _execute_docker_stage(self, stage, plugin_config, previous_results):
        docker_config = stage.get('docker', {})

        image_name, error = self.docker_orchestrator.get_image(plugin_config.get('name'), plugin_config)
        if error:
            return None, error

        volumes = docker_config.get('volumes', [])
        volume_list = self.docker_orchestrator.prepare_volumes(volumes, self.temp_dir, self.output_dir)

        command = docker_config.get('command', [])
        command_resolved = [self.connector_engine.substitute_variables(str(c), self.variables) for c in command]

        environment = docker_config.get('environment', {})
        env_resolved = {k: self.connector_engine.substitute_variables(str(v), self.variables) for k, v in environment.items()}

        timeout = docker_config.get('timeout')

        result, error = self.docker_orchestrator.run_container(image_name, command_resolved, volume_list, env_resolved, timeout)

        return result, error

    def _execute_extract_stage(self, stage, plugin_config, previous_results):
        tasks = stage.get('tasks', [])
        outputs = {}

        for task in tasks:
            task_name = task.get('name')
            connector_name = task.get('connector')
            config = task.get('config', {})

            config_resolved = self._resolve_variables(config)
            input_data = config_resolved.get('input')

            result, error = self.connector_engine.execute_connector(connector_name, input_data, config_resolved)
            if error:
                return None, f'task_{task_name}_failed: {error}'

            output_key = task.get('output')
            if output_key:
                outputs[output_key] = result

        return outputs, None

    def _create_default_workflow(self, plugin_config):
        interface = plugin_config.get('interface', {})

        prepare_tasks = []
        inputs = interface.get('inputs', [])
        for inp in inputs:
            input_type = inp.get('type')
            if input_type == 'directory':
                prepare_tasks.append({'name': f'prepare_{input_type}', 'connector': 'identity', 'config': {'input': '${DATASET_PATH}'}, 'output': input_type})

        docker_config = {'image': plugin_config.get('docker', {}).get('image'), 'command': interface.get('command', []), 'volumes': interface.get('volumes', []), 'timeout': plugin_config.get('execution', {}).get('timeout')}

        extract_tasks = []
        outputs = interface.get('outputs', [])
        for out in outputs:
            output_type = out.get('type')
            format_type = out.get('format')
            file_path = out.get('file')
            if output_type == 'trajectory':
                extract_tasks.append({'name': 'parse_trajectory', 'connector': f'{format_type}_trajectory', 'config': {'input': f'${{OUTPUT_DIR}}/{file_path}'}, 'output': 'trajectory'})

        workflow = {'stages': [{'name': 'prepare', 'type': 'prepare', 'tasks': prepare_tasks}, {'name': 'execute', 'type': 'execute', 'docker': docker_config}, {'name': 'extract', 'type': 'extract', 'tasks': extract_tasks}]}

        return workflow

    def _resolve_variables(self, config):
        if isinstance(config, dict):
            return {k: self._resolve_variables(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_variables(item) for item in config]
        elif isinstance(config, str):
            return self.connector_engine.substitute_variables(config, self.variables)
        return config

    def _cleanup(self):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
