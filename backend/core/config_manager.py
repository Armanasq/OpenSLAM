class ConfigManager:
    def __init__(self, config):
        self.config = config
        self.watchers = []
    def reload(self):
        result = self.config.reload()
        if "error" in result:
            return result
        self.broadcast()
        return {"status": "ok"}
    def broadcast(self):
        for watcher in self.watchers:
            watcher.notify(self.config.data)
    def subscribe(self, watcher):
        self.watchers.append(watcher)
