import os
import json
from shared.errors import format_error
class PluginDiscovery:
    def __init__(self, config):
        self.config = config
        self.plugins = {}
    def scan(self):
        algorithms_dir = self.config.get("paths.algorithms_dir")
        if not algorithms_dir:
            return format_error("Algorithms directory not configured", 1004, {})
        if not os.path.exists(algorithms_dir):
            os.makedirs(algorithms_dir)
            return {"status": "ok", "plugins": {}}
        for dir in os.listdir(algorithms_dir):
            path = f"{algorithms_dir}/{dir}"
            if os.path.isdir(path):
                validation_result = self.validate_structure(path)
                if validation_result:
                    metadata_result = self.extract_metadata(path)
                    if "error" not in metadata_result:
                        self.plugins[dir] = metadata_result
        return {"status": "ok", "plugins": self.plugins}
    def validate_structure(self, path):
        required = ["config.json", "launcher.py"]
        for file in required:
            if not os.path.exists(f"{path}/{file}"):
                return False
        return True
    def extract_metadata(self, path):
        config_path = f"{path}/config.json"
        if not os.path.exists(config_path):
            return format_error("Plugin config not found", 1005, {"path": config_path})
        config_file = open(config_path, "r")
        config_content = config_file.read()
        config_file.close()
        plugin_config = json.loads(config_content)
        if "name" not in plugin_config:
            return format_error("Plugin name missing", 1005, {"path": config_path})
        if "type" not in plugin_config:
            return format_error("Plugin type missing", 1005, {"path": config_path})
        return {"name": plugin_config["name"], "type": plugin_config["type"], "path": path, "config": plugin_config}
