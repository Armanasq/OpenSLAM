import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config import Config
from backend.core.config_manager import ConfigManager
from backend.core.structure_validator import validate_structure
from backend.core.plugin_discovery import PluginDiscovery
from backend.core.algorithm_loader import AlgorithmLoader
config = Config()
load_result = config.load("development")
if "error" in load_result:
    print(f"Config load error: {load_result}")
    exit(1)
structure_result = validate_structure(config)
if "error" in structure_result:
    print(f"Structure validation error: {structure_result}")
    exit(1)
manager = ConfigManager(config)
discovery = PluginDiscovery(config)
scan_result = discovery.scan()
if "error" in scan_result:
    print(f"Plugin scan error: {scan_result}")
    exit(1)
loader = AlgorithmLoader(discovery)
app = FastAPI(title="OpenSLAM Backend", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
from backend.api.routes import router
app.include_router(router, prefix="/api")
from fastapi import WebSocket, WebSocketDisconnect
connections = []
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        connections.remove(websocket)
if __name__ == "__main__":
    import uvicorn
    backend_host = config.get("server.backend_host")
    backend_port = config.get("server.backend_port")
    print(f"Backend ready on {backend_host}:{backend_port}")
    print(f"Plugins discovered: {len(discovery.plugins)}")
    uvicorn.run(app, host=backend_host, port=backend_port)