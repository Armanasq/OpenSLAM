import time
import json
import os
def get_error_code(name, config):
    return config.get(f"error_codes.{name}")
def format_error(error, code, details):
    recovery = get_recovery_instruction(code)
    return {"error": error, "code": code, "details": details, "recovery": recovery}
def get_recovery_instruction(code):
    instructions = {1001: "Validate input data and retry", 1002: "Check path exists and retry", 1003: "Check logs for details", 1004: "Check config file syntax", 1005: "Check plugin structure"}
    if code in instructions:
        return instructions[code]
    return "Contact support"
def log_error(error_dict):
    timestamp = time.time()
    log_entry = {"timestamp": timestamp, "error": error_dict}
    log_path = "logs/errors.log"
    if not os.path.exists("logs"):
        os.makedirs("logs")
    log_file = open(log_path, "a")
    log_file.write(json.dumps(log_entry) + "\n")
    log_file.close()
    return {"status": "ok"}
