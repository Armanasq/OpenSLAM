import re
def format_code(code):
    lines = code.split("\n")
    formatted = []
    for line in lines:
        if line.strip():
            formatted.append(line)
    return "\n".join(formatted)
def remove_empty_lines(code):
    lines = code.split("\n")
    result = []
    for line in lines:
        if line.strip():
            result.append(line)
    return "\n".join(result)
def validate_naming(name):
    adjectives = ["quick", "fast", "slow", "big", "small", "good", "bad", "new", "old", "high", "low", "long", "short", "early", "late", "easy", "hard", "simple", "complex"]
    adverbs = ["quickly", "slowly", "easily", "hardly", "simply", "really", "very", "quite", "just", "only", "also", "even", "still", "already"]
    words = name.lower().split("_")
    for word in words:
        if word in adjectives or word in adverbs:
            return {"error": f"Name contains adjective/adverb: {word}", "code": 1001, "details": {"name": name, "word": word}, "recovery": "Validate input data and retry"}
    return {"status": "ok"}
def check_single_line_dict(code):
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if "{" in line and "}" not in line:
            next_line_index = i + 1
            if next_line_index < len(lines) and "}" in lines[next_line_index]:
                return {"error": f"Multi-line dict at line {i+1}", "code": 1001, "details": {"line": i+1}, "recovery": "Validate input data and retry"}
    return {"status": "ok"}
