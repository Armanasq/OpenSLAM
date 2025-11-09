import importlib
from shared.errors import format_error
class AlgorithmLoader:
    def __init__(self, discovery):
        self.discovery = discovery
        self.loaded = {}
    def load(self, name):
        if name in self.loaded:
            return {"status": "ok", "module": self.loaded[name]}
        if name not in self.discovery.plugins:
            return format_error("Plugin not found", 1002, {"name": name})
        metadata = self.discovery.plugins[name]
        module_path = f"{metadata['path']}.launcher".replace("/", ".")
        module = importlib.import_module(module_path)
        self.loaded[name] = module
        return {"status": "ok", "module": module}
    def reload(self):
        scan_result = self.discovery.scan()
        if "error" in scan_result:
            return scan_result
        self.loaded = {}
        return {"status": "ok"}
