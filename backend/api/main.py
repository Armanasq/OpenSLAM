import sys
import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json
from datetime import datetime
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from backend.core.dataset_manager import DatasetManager, ValidationError
from backend.core.algorithm_registry import AlgorithmRegistry
from backend.core.code_executor import CodeExecutor
from backend.core.performance_analyzer import TrajectoryErrorComputer, ErrorPlotGenerator, PerformanceMetricsDisplay
from backend.core.performance_comparison import AlgorithmComparison, MetricDefinitions
from backend.core.tutorial_manager import TutorialManager
from backend.core.algorithm_loader import AlgorithmLoader
from config.settings import BASE_DIR, FRONTEND_DIR
app = FastAPI(title="OpenSLAM API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
dataset_manager = DatasetManager()
algorithm_registry = AlgorithmRegistry()
code_executor = CodeExecutor()
performance_analyzer = PerformanceMetricsDisplay()
algorithm_comparison = AlgorithmComparison()
tutorial_manager = TutorialManager()
algorithm_loader = AlgorithmLoader()
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass
manager = ConnectionManager()
class DatasetLoadRequest(BaseModel):
    path: str
class AlgorithmCreateRequest(BaseModel):
    name: str
    type: str
    code: str
    parameters: Dict[str, Any] = {}
class AlgorithmExecuteRequest(BaseModel):
    algorithm_id: str
    dataset_id: str
    parameters: Dict[str, Any] = {}
class CodeValidationRequest(BaseModel):
    code: str
    algorithm_type: str
class ComparisonRequest(BaseModel):
    result_ids: List[str]
class ExportRequest(BaseModel):
    comparison_id: str
    format: str

class DirectoryBrowseRequest(BaseModel):
    path: str
@app.get("/")
async def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "build", "index.html"))
@app.get("/api/datasets")
async def get_datasets():
    datasets = dataset_manager.list_datasets()
    return datasets

@app.post("/api/browse-directory")
async def browse_directory(request: DirectoryBrowseRequest):
    try:
        path = request.path if request.path else "/"
        
        # Ensure path exists, fallback to common directories
        if not os.path.exists(path):
            for fallback in ["/home", "/", "/tmp"]:
                if os.path.exists(fallback):
                    path = fallback
                    break
        
        items = []
        
        # Add parent directory option (except for root)
        if path != "/" and path != "":
            parent_path = os.path.dirname(path)
            items.append({
                "name": "..",
                "path": parent_path,
                "type": "directory",
                "is_parent": True
            })
        
        # List directories
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                try:
                    if os.path.isdir(item_path) and not item.startswith('.'):
                        items.append({
                            "name": item,
                            "path": item_path,
                            "type": "directory",
                            "is_parent": False
                        })
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            # If we can't read the directory, try some common subdirectories
            common_dirs = ["home", "usr", "var", "tmp", "opt"]
            for dir_name in common_dirs:
                dir_path = os.path.join(path, dir_name)
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    items.append({
                        "name": dir_name,
                        "path": dir_path,
                        "type": "directory",
                        "is_parent": False
                    })
            
        return {
            "current_path": path,
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/datasets/{dataset_id}/details")
async def get_dataset_details(dataset_id: str):
    dataset = dataset_manager.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"dataset": dataset, "metadata": dataset.metadata}

@app.post("/api/datasets/load")
async def load_dataset(request: DatasetLoadRequest):
    try:
        if not request.path:
            raise HTTPException(status_code=400, detail={"message": "Dataset path is required", "errors": ["Path cannot be empty"]})
        dataset = dataset_manager.load_kitti_dataset(request.path)
        await manager.broadcast(json.dumps({"type": "dataset_loaded", "payload": {"id": dataset.id, "name": dataset.name}}))
        return {"id": dataset.id, "name": dataset.name, "format": dataset.format, "sequence_length": dataset.sequence_length, "sensors": dataset.sensors, "created_at": dataset.created_at.isoformat()}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "errors": e.errors})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/datasets/{dataset_id}/validate")
async def validate_dataset(dataset_id: str):
    dataset = dataset_manager.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        is_valid, errors = dataset_manager.validate_kitti_format(dataset.file_paths["root"])
        return {"valid": is_valid, "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/datasets/{dataset_id}/frame/{frame_id}/{sensor}")
async def get_frame_image(dataset_id: str, frame_id: int, sensor: str):
    dataset = dataset_manager.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    image_path = dataset_manager.get_sensor_data_path(dataset_id, sensor, frame_id)
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)
@app.get("/api/datasets/{dataset_id}/ground-truth")
async def get_ground_truth(dataset_id: str):
    dataset = dataset_manager.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.metadata.get("has_ground_truth", False):
        raise HTTPException(status_code=404, detail="No ground truth available")
    poses_path = dataset.file_paths.get("poses")
    if not poses_path or not os.path.exists(poses_path):
        raise HTTPException(status_code=404, detail="Ground truth file not found")
    trajectory = []
    with open(poses_path, 'r') as f:
        for i, line in enumerate(f):
            values = [float(x) for x in line.split()]
            pose_matrix = [[values[j*4 + k] for k in range(4)] + ([0, 0, 0, 1] if j == 2 else []) for j in range(3)]
            if len(pose_matrix[2]) == 3:
                pose_matrix.append([0, 0, 0, 1])
            trajectory.append({"frame_id": i, "pose": pose_matrix, "position": [values[3], values[7], values[11]]})
    return {"trajectory": trajectory}

@app.get("/api/datasets/{dataset_id}/lidar/{frame_id}")
async def get_lidar_data(dataset_id: str, frame_id: int, resolution: int = 10000):
    dataset = dataset_manager.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if "velodyne" not in dataset.sensors:
        raise HTTPException(status_code=404, detail="Lidar data not available")
    lidar_data = dataset_manager.load_lidar_data(dataset_id, frame_id)
    if lidar_data is None:
        raise HTTPException(status_code=404, detail="Lidar frame not found")
    if resolution < len(lidar_data):
        step = max(1, len(lidar_data) // resolution)
        lidar_data = lidar_data[::step]
    return {
        "x": lidar_data[:, 0].tolist(),
        "y": lidar_data[:, 1].tolist(), 
        "z": lidar_data[:, 2].tolist(),
        "intensity": lidar_data[:, 3].tolist() if lidar_data.shape[1] > 3 else [0.5] * len(lidar_data)
    }
@app.get("/api/algorithms/library")
async def get_algorithm_library():
    algorithms = algorithm_loader.discover_algorithms()
    return algorithms

@app.get("/api/algorithm-templates")
async def get_algorithm_templates():
    templates = algorithm_registry.list_templates()
    return [{"id": template, "name": template.replace('_', ' ').title()} for template in templates]
@app.get("/api/algorithm-templates/{template_id}")
async def get_algorithm_template(template_id: str):
    from backend.core.algorithm_registry import AlgorithmTemplate
    template = AlgorithmTemplate(template_id, algorithm_registry)
    return {"skeleton_code": template.generate_skeleton_code(), "method_signatures": template.get_method_signatures(), "default_parameters": template.get_default_parameters()}
@app.post("/api/algorithms")
async def create_algorithm(request: AlgorithmCreateRequest):
    algorithm_data = {"id": f"alg_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "name": request.name, "type": request.type, "code": request.code, "parameters": request.parameters, "created_at": datetime.now(), "updated_at": datetime.now()}
    return algorithm_data
@app.post("/api/validate-code")
async def validate_code(request: CodeValidationRequest):
    try:
        result = code_executor.execute_code(request.code)
        return {"valid": result.success, "errors": [result.error] if result.error else []}
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}
@app.post("/api/algorithms/{plugin_id}/load")
async def load_algorithm_plugin(plugin_id: str):
    try:
        algorithm = algorithm_loader.load_algorithm(plugin_id)
        if algorithm is None:
            raise HTTPException(status_code=404, detail="Algorithm not found or failed to load")
        return {"status": "loaded", "plugin_id": plugin_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute-algorithm")
async def execute_algorithm(request: AlgorithmExecuteRequest):
    try:
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        asyncio.create_task(run_algorithm_execution(execution_id, request))
        return {"execution_id": execution_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
async def run_algorithm_execution(execution_id: str, request: AlgorithmExecuteRequest):
    try:
        await asyncio.sleep(2)
        result = {"id": execution_id, "algorithm_name": f"Algorithm_{request.algorithm_id}", "dataset_name": f"Dataset_{request.dataset_id}", "success": True, "execution_time": 15.5, "frames_processed": 100, "metrics": {"ate": 0.125, "rpe_trans": 0.045, "rpe_rot": 0.012}, "timestamp": datetime.now().isoformat()}
        await manager.broadcast(json.dumps({"type": "algorithm_result", "payload": result}))
    except Exception as e:
        await manager.broadcast(json.dumps({"type": "error", "message": str(e)}))
@app.get("/api/results/{result_id}/visualization")
async def get_visualization_data(result_id: str):
    trajectory = [{"frame_id": i, "position": [i * 0.1, i * 0.05, 0], "pose": [[1, 0, 0, i * 0.1], [0, 1, 0, i * 0.05], [0, 0, 1, 0], [0, 0, 0, 1]]} for i in range(100)]
    point_cloud = [{"x": i * 0.1, "y": j * 0.1, "z": 0, "intensity": 0.5} for i in range(50) for j in range(50)]
    return {"trajectory": trajectory, "point_cloud": point_cloud}
@app.post("/api/results/{result_id}/export")
async def export_visualization(result_id: str, request: dict):
    return {"message": "Export functionality not implemented"}
@app.post("/api/analysis/compare")
async def compare_algorithms(request: ComparisonRequest):
    comparison_data = {"comparison_id": f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "algorithms": {}, "rankings": {"overall": []}, "summary": {"best_ate": {"algorithm_id": "alg1", "value": 0.1}}}
    return comparison_data
@app.get("/api/analysis/plots/{comparison_id}")
async def get_comparison_plots(comparison_id: str):
    return {"metrics_comparison": "base64_encoded_plot_data", "trajectory_comparison": "base64_encoded_plot_data"}
@app.post("/api/analysis/report")
async def generate_analysis_report(request: dict):
    return {"report_id": "report_123", "generated_at": datetime.now().isoformat()}
@app.post("/api/analysis/export")
async def export_analysis(request: ExportRequest):
    return {"message": "Export functionality not implemented"}
@app.get("/api/tutorials")
async def get_tutorials():
    tutorials = tutorial_manager.get_tutorial_list("default_user")
    return tutorials
@app.get("/api/tutorials/{tutorial_id}")
async def get_tutorial(tutorial_id: str):
    result = tutorial_manager.start_tutorial("default_user", tutorial_id)
    return result
@app.get("/api/tutorials/{tutorial_id}/step/{step_index}")
async def get_tutorial_step(tutorial_id: str, step_index: int):
    result = tutorial_manager.get_tutorial_step("default_user", tutorial_id, step_index)
    return result
@app.post("/api/tutorials/{tutorial_id}/step/{step_index}/submit")
async def submit_tutorial_solution(tutorial_id: str, step_index: int, request: dict):
    code = request.get("code", "")
    execution_result = code_executor.execute_code(code)
    result = tutorial_manager.submit_step_solution("default_user", tutorial_id, step_index, code, {"success": execution_result.success, "output": execution_result.output, "error": execution_result.error})
    return result
@app.post("/api/execute-code")
async def execute_code_endpoint(request: dict):
    code = request.get("code", "")
    context = request.get("context", "general")
    result = code_executor.execute_code(code)
    return {"success": result.success, "output": result.output, "error": result.error, "execution_time": result.execution_time}
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await manager.send_personal_message(json.dumps({"type": "pong"}), websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
@app.websocket("/ws/execution")
async def execution_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    from backend.core.terminal_manager import terminal_manager
    
    await manager.connect(websocket)
    session_id = f"session_{id(websocket)}"
    
    # Set up output callback
    async def output_callback(output: str):
        try:
            await manager.send_personal_message(
                json.dumps({"type": "output", "content": output}),
                websocket
            )
        except:
            pass
    
    terminal_manager.set_output_callback(session_id, output_callback)
    
    # Create terminal session
    work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    success = terminal_manager.create_session(session_id, work_dir)
    
    if success:
        await manager.send_personal_message(
            json.dumps({"type": "system", "content": f"Terminal session started in {work_dir}"}),
            websocket
        )
    else:
        await manager.send_personal_message(
            json.dumps({"type": "error", "content": "Failed to start terminal session"}),
            websocket
        )
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "command":
                command = message.get("command", "")
                terminal_manager.execute_command(session_id, command)
            elif message.get("type") == "resize":
                cols = message.get("cols", 120)
                rows = message.get("rows", 30)
                if session_id in terminal_manager.sessions:
                    terminal_manager.sessions[session_id].resize(cols, rows)
                    
    except WebSocketDisconnect:
        terminal_manager.close_session(session_id)
        manager.disconnect(websocket)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)