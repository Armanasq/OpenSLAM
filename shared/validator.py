import json
def validate_schema(data, schema):
    for key in schema:
        if key not in data:
            if "required" in schema[key]:
                return {"error": f"Missing required key: {key}", "code": 1004, "details": {"key": key}, "recovery": "Check config file syntax"}
        if key in data:
            if schema[key]["type"] == "object":
                if not isinstance(data[key], dict):
                    return {"error": f"Invalid type for {key}", "code": 1004, "details": {"key": key, "expected": "object", "got": type(data[key]).__name__}, "recovery": "Check config file syntax"}
                if "required" in schema[key]:
                    for req in schema[key]["required"]:
                        if req not in data[key]:
                            return {"error": f"Missing required field: {key}.{req}", "code": 1004, "details": {"key": f"{key}.{req}"}, "recovery": "Check config file syntax"}
                if "properties" in schema[key]:
                    for prop in schema[key]["properties"]:
                        if prop in data[key]:
                            expected_type = schema[key]["properties"][prop]["type"]
                            actual_value = data[key][prop]
                            if expected_type == "integer" and not isinstance(actual_value, int):
                                return {"error": f"Invalid type for {key}.{prop}", "code": 1004, "details": {"key": f"{key}.{prop}", "expected": "integer", "got": type(actual_value).__name__}, "recovery": "Check config file syntax"}
                            if expected_type == "string" and not isinstance(actual_value, str):
                                return {"error": f"Invalid type for {key}.{prop}", "code": 1004, "details": {"key": f"{key}.{prop}", "expected": "string", "got": type(actual_value).__name__}, "recovery": "Check config file syntax"}
                            if expected_type == "array" and not isinstance(actual_value, list):
                                return {"error": f"Invalid type for {key}.{prop}", "code": 1004, "details": {"key": f"{key}.{prop}", "expected": "array", "got": type(actual_value).__name__}, "recovery": "Check config file syntax"}
            if schema[key]["type"] == "array" and not isinstance(data[key], list):
                return {"error": f"Invalid type for {key}", "code": 1004, "details": {"key": key, "expected": "array", "got": type(data[key]).__name__}, "recovery": "Check config file syntax"}
    return {"status": "ok"}
def merge(base, override):
    result = base.copy()
    for key in override:
        if key in result and isinstance(result[key], dict) and isinstance(override[key], dict):
            result[key] = merge(result[key], override[key])
        else:
            result[key] = override[key]
    return result
def navigate(data, path):
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current
