import sys
import yaml
import importlib.util
from pathlib import Path
from config import plugin_config as pcfg
from config import openslam_config as cfg
class PluginManager:
    def __init__(self, plugin_dir=None):
        self.plugin_dir = Path(plugin_dir) if plugin_dir else Path(pcfg.PLUGIN_DIR)
        self.plugins = {}
        self.loaded_modules = {}
    def discover_plugins(self):
        if not self.plugin_dir.exists():
            return {}, 'plugin_directory_not_found'
        discovered = {}
        for plugin_path in self.plugin_dir.iterdir():
            if not plugin_path.is_dir():
                continue
            config_path = plugin_path / pcfg.CONFIG_FILENAME
            if not config_path.exists():
                continue
            config, error = self.load_plugin_config(config_path)
            if error:
                continue
            plugin_name = plugin_path.name
            discovered[plugin_name] = {'path': plugin_path, 'config': config}
        return discovered, None
    def load_plugin_config(self, config_path):
        if not config_path.exists():
            return None, 'config_not_found'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        validation_result, error = self.validate_plugin_config(config)
        if error:
            return None, error
        return config, None
    def validate_plugin_config(self, config):
        required_fields = ['name', 'version', 'input_types', 'output_format']
        for field in required_fields:
            if field not in config:
                return None, f'missing_required_field_{field}'
        is_workflow = 'workflow' in config or 'interface' in config
        is_cpp = config.get('language') == 'cpp'
        if not is_workflow and not is_cpp:
            if 'entry_point' not in config:
                return None, 'missing_required_field_entry_point'
            if 'functions' not in config:
                return None, 'missing_required_field_functions'
            for required_func in pcfg.REQUIRED_FUNCTIONS:
                if required_func not in config['functions']:
                    return None, f'missing_required_function_{required_func}'
        elif is_cpp and not is_workflow:
            if 'cpp_wrapper' not in config:
                return None, 'missing_required_field_cpp_wrapper'
        if config.get('input_types'):
            for input_type in config['input_types']:
                if input_type not in pcfg.SUPPORTED_INPUT_TYPES:
                    return None, f'unsupported_input_type_{input_type}'
        if config.get('output_format') not in pcfg.SUPPORTED_OUTPUT_FORMATS:
            return None, f'unsupported_output_format_{config.get("output_format")}'
        return True, None
    def load_plugin(self, plugin_name):
        if plugin_name in self.plugins:
            return self.plugins[plugin_name], None
        discovered, error = self.discover_plugins()
        if error:
            return None, error
        if plugin_name not in discovered:
            return None, 'plugin_not_found'
        plugin_info = discovered[plugin_name]
        plugin_path = plugin_info['path']
        config = plugin_info['config']
        is_workflow = 'workflow' in config or 'interface' in config
        is_cpp = config.get('language') == 'cpp'
        if is_workflow or is_cpp:
            plugin = {'name': plugin_name, 'config': config, 'module': None, 'path': plugin_path}
            self.plugins[plugin_name] = plugin
            return plugin, None
        entry_point = config['entry_point']
        module_path = plugin_path / entry_point
        if not module_path.exists():
            return None, 'entry_point_not_found'
        spec = importlib.util.spec_from_file_location(f'plugin_{plugin_name}', module_path)
        if spec is None or spec.loader is None:
            return None, 'module_load_failed'
        module = importlib.util.module_from_spec(spec)
        sys.modules[f'plugin_{plugin_name}'] = module
        spec.loader.exec_module(module)
        self.loaded_modules[plugin_name] = module
        plugin = {'name': plugin_name, 'config': config, 'module': module, 'path': plugin_path}
        self.plugins[plugin_name] = plugin
        return plugin, None
    def get_plugin_function(self, plugin, function_name):
        if function_name not in plugin['config']['functions']:
            return None, f'function_not_defined_{function_name}'
        function_mapping = plugin['config']['functions'][function_name]
        if isinstance(function_mapping, str):
            func_name = function_mapping
        elif isinstance(function_mapping, dict):
            func_name = function_mapping.get('name')
        else:
            return None, 'invalid_function_mapping'
        module = plugin['module']
        if not hasattr(module, func_name):
            return None, f'function_not_found_{func_name}'
        return getattr(module, func_name), None
    def list_plugins(self):
        discovered, error = self.discover_plugins()
        if error:
            return [], error
        plugin_list = []
        for name, info in discovered.items():
            config = info['config']
            plugin_list.append({'name': name, 'version': config.get('version', 'unknown'), 'description': config.get('description', ''), 'input_types': config.get('input_types', []), 'output_format': config.get('output_format', '')})
        return plugin_list, None
    def get_data_adapter(self, plugin, dataset_format, dataset):
        config = plugin['config']
        if 'data_adapters' in config and dataset_format in config['data_adapters']:
            adapter_name = config['data_adapters'][dataset_format]
            module = plugin['module']
            if hasattr(module, adapter_name):
                adapter_class = getattr(module, adapter_name)
                return adapter_class(dataset), None
        return None, f'no_adapter_for_{dataset_format}'
