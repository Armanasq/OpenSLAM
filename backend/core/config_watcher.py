from shared.models import create_message
class ConfigWatcher:
    def __init__(self, ws_handler):
        self.ws_handler = ws_handler
    def notify(self, config_data):
        message = create_message("config_update", config_data)
        self.ws_handler.broadcast(message)
