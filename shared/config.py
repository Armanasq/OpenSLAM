import json
import os
from shared.validator import validate_schema, merge, navigate
class Config:
    def __init__(self):
        self.data = {}
        self.env = None
    def load(self, env):
        self.env = env
        base_path = "config/base.json"
        if not os.path.exists(base_path):
            return {"error": "Base config not found", "code": 1004, "details": {"path": base_path}, "recovery": "Check config file syntax"}
        base_file = open(base_path, "r")
        base_content = base_file.read()
        base_file.close()
        base = json.loads(base_content)
        override_path = f"config/{env}.json"
        if os.path.exists(override_path):
            override_file = open(override_path, "r")
            override_content = override_file.read()
            override_file.close()
            override = json.loads(override_content)
            self.data = merge(base, override)
        else:
            self.data = base
        validation_result = self.validate()
        if "error" in validation_result:
            return validation_result
        return {"status": "ok"}
    def get(self, path):
        return navigate(self.data, path)
    def reload(self):
        if self.env:
            return self.load(self.env)
        return {"error": "No environment set", "code": 1004, "details": {}, "recovery": "Check config file syntax"}
    def validate(self):
        schema_path = "config/schema.json"
        if not os.path.exists(schema_path):
            return {"error": "Schema not found", "code": 1004, "details": {"path": schema_path}, "recovery": "Check config file syntax"}
        schema_file = open(schema_path, "r")
        schema_content = schema_file.read()
        schema_file.close()
        schema = json.loads(schema_content)
        return validate_schema(self.data, schema)
