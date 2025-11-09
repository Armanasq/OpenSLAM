import os
from shared.errors import format_error
def validate_structure(config):
    required_dirs = [config.get("paths.config_dir"), config.get("paths.shared_dir"), config.get("paths.backend_dir"), config.get("paths.frontend_dir"), config.get("paths.algorithms_dir"), config.get("paths.tools_dir")]
    required_files = ["config/base.json", "config/schema.json", "shared/config.py"]
    for dir in required_dirs:
        if dir and not os.path.exists(dir):
            os.makedirs(dir)
    for file in required_files:
        if not os.path.exists(file):
            return format_error(f"Required file missing: {file}", 1004, {"file": file})
    return {"status": "ok"}
