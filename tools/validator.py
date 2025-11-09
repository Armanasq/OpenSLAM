import re
def check_hardcoded_values(code):
    lines = code.split("\n")
    issues = []
    for i, line in enumerate(lines):
        if "= 8007" in line or "= 3001" in line or '= "localhost"' in line or '= "0.0.0.0"' in line:
            if "config" not in line:
                issues.append({"line": i+1, "content": line.strip()})
    if issues:
        return {"error": "Hardcoded values found", "code": 1001, "details": {"issues": issues}, "recovery": "Validate input data and retry"}
    return {"status": "ok"}
def check_try_except(code):
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if "try:" in line or "except" in line:
            return {"error": f"try-except block at line {i+1}", "code": 1001, "details": {"line": i+1}, "recovery": "Validate input data and retry"}
    return {"status": "ok"}
def check_typing(code):
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if ": int" in line or ": str" in line or ": dict" in line or ": list" in line or "-> " in line:
            return {"error": f"Type annotation at line {i+1}", "code": 1001, "details": {"line": i+1}, "recovery": "Validate input data and retry"}
    return {"status": "ok"}
def check_dataclasses(code):
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if "@dataclass" in line or "from dataclasses import" in line:
            return {"error": f"Dataclass usage at line {i+1}", "code": 1001, "details": {"line": i+1}, "recovery": "Validate input data and retry"}
    return {"status": "ok"}
def check_naming_conventions(code):
    lines = code.split("\n")
    issues = []
    for i, line in enumerate(lines):
        if "def " in line:
            match = re.search(r"def (\w+)\(", line)
            if match:
                func_name = match.group(1)
                adjectives = ["quick", "fast", "slow", "big", "small", "good", "bad", "new", "old"]
                for adj in adjectives:
                    if adj in func_name.lower():
                        issues.append({"line": i+1, "name": func_name, "issue": f"Contains adjective: {adj}"})
    if issues:
        return {"error": "Naming convention violations", "code": 1001, "details": {"issues": issues}, "recovery": "Validate input data and retry"}
    return {"status": "ok"}
