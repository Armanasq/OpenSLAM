import time
import uuid
def create_websocket_message(msg_type, payload):
    return {"type": msg_type, "payload": payload, "timestamp": int(time.time()), "id": str(uuid.uuid4())}
def create_api_response(data):
    return {"data": data, "timestamp": int(time.time()), "status": "ok"}
def validate_message_format(message):
    if not isinstance(message, dict):
        return {"error": "Message must be dict", "code": 1001, "details": {"type": type(message).__name__}, "recovery": "Validate input data and retry"}
    required_fields = ["type", "payload", "timestamp", "id"]
    for field in required_fields:
        if field not in message:
            return {"error": f"Missing field: {field}", "code": 1001, "details": {"field": field}, "recovery": "Validate input data and retry"}
    if not isinstance(message["type"], str):
        return {"error": "Type must be string", "code": 1001, "details": {"type": type(message["type"]).__name__}, "recovery": "Validate input data and retry"}
    if not isinstance(message["payload"], dict):
        return {"error": "Payload must be dict", "code": 1001, "details": {"type": type(message["payload"]).__name__}, "recovery": "Validate input data and retry"}
    if not isinstance(message["timestamp"], int):
        return {"error": "Timestamp must be int", "code": 1001, "details": {"type": type(message["timestamp"]).__name__}, "recovery": "Validate input data and retry"}
    if not isinstance(message["id"], str):
        return {"error": "ID must be string", "code": 1001, "details": {"type": type(message["id"]).__name__}, "recovery": "Validate input data and retry"}
    return {"status": "ok"}
