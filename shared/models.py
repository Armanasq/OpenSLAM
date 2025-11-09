import time
import uuid
from shared.errors import get_recovery_instruction
def create_dataset(id, name, format, length, sensors, calibration, metadata, created, paths):
    return {"id": id, "name": name, "format": format, "sequence_length": length, "sensors": sensors, "calibration": calibration, "metadata": metadata, "created_at": created, "file_paths": paths}
def create_algorithm(id, name, type, code, params, created, updated):
    return {"id": id, "name": name, "type": type, "source_code": code, "parameters": params, "created_at": created, "updated_at": updated}
def create_message(msg_type, payload):
    return {"type": msg_type, "payload": payload, "timestamp": int(time.time()), "id": generate_id()}
def create_error(error, code, details):
    recovery = get_recovery_instruction(code)
    return {"error": error, "code": code, "details": details, "recovery": recovery}
def generate_id():
    return str(uuid.uuid4())
def create_execution(id, algorithm_id, dataset_id, frame_range, status, results, metrics, started, completed):
    return {"id": id, "algorithm_id": algorithm_id, "dataset_id": dataset_id, "frame_range": frame_range, "status": status, "results": results, "metrics": metrics, "started_at": started, "completed_at": completed}
def create_trajectory_point(position, orientation, timestamp, frame_id):
    return {"position": position, "orientation": orientation, "timestamp": timestamp, "frame_id": frame_id}
def create_performance_metrics(ate, rpe_trans, rpe_rot, execution_time, memory_usage):
    return {"ate": ate, "rpe_trans": rpe_trans, "rpe_rot": rpe_rot, "execution_time": execution_time, "memory_usage": memory_usage}