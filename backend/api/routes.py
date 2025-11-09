from fastapi import APIRouter
from shared.protocol import create_api_response
from shared.errors import format_error
from backend.core.dataset_manager import DatasetManager
dataset_manager = DatasetManager()
router = APIRouter()
@router.get("/datasets")
async def get_datasets():
    datasets = dataset_manager.list_datasets()
    return create_api_response(datasets)
@router.get("/datasets/{dataset_id}/details")
async def get_dataset_details(dataset_id: str):
    dataset = dataset_manager.get_dataset(dataset_id)
    if not dataset:
        return format_error("Dataset not found", 1002, {"dataset_id": dataset_id})
    return create_api_response(dataset)
@router.post("/datasets/load")
async def load_dataset(request: dict):
    path = request.get("path")
    if not path:
        return format_error("Path is required", 1001, {"field": "path"})
    result = dataset_manager.load_kitti_dataset(path)
    if "error" in result:
        return result
    return create_api_response(result)
@router.get("/datasets/{dataset_id}/ground-truth")
async def get_ground_truth(dataset_id: str):
    dataset = dataset_manager.get_dataset(dataset_id)
    if not dataset:
        return format_error("Dataset not found", 1002, {"dataset_id": dataset_id})
    if not dataset.get("metadata", {}).get("has_ground_truth"):
        return format_error("Dataset has no ground truth", 1002, {"dataset_id": dataset_id})
    frames = dataset_manager.load_frame_range(dataset_id, 0, dataset["sequence_length"])
    trajectory = []
    for frame in frames:
        if "ground_truth_pose" in frame:
            pose_matrix = frame["ground_truth_pose"]
            pose_list = [[float(pose_matrix[0][0]), float(pose_matrix[0][1]), float(pose_matrix[0][2]), float(pose_matrix[0][3])], [float(pose_matrix[1][0]), float(pose_matrix[1][1]), float(pose_matrix[1][2]), float(pose_matrix[1][3])], [float(pose_matrix[2][0]), float(pose_matrix[2][1]), float(pose_matrix[2][2]), float(pose_matrix[2][3])]]
            trajectory.append({"position": [float(pose_matrix[0][3]), float(pose_matrix[1][3]), float(pose_matrix[2][3])], "pose": pose_list, "frame_id": frame["frame_id"]})
    return {"trajectory": trajectory}
@router.get("/datasets/{dataset_id}/lidar/{frame_id}")
async def get_lidar_data(dataset_id: str, frame_id: int, resolution: int = 10000):
    lidar_data = dataset_manager.load_lidar_data(dataset_id, frame_id)
    if lidar_data is None:
        return format_error("Lidar data not found", 1002, {"dataset_id": dataset_id, "frame_id": frame_id})
    if len(lidar_data) > resolution:
        import numpy as np
        indices = np.random.choice(len(lidar_data), resolution, replace=False)
        lidar_data = lidar_data[indices]
    return {"x": lidar_data[:, 0].tolist(), "y": lidar_data[:, 1].tolist(), "z": lidar_data[:, 2].tolist(), "intensity": lidar_data[:, 3].tolist()}
@router.get("/datasets/{dataset_id}/frame/{frame_id}/{sensor}")
async def get_frame_image(dataset_id: str, frame_id: int, sensor: str):
    from fastapi.responses import FileResponse
    import os
    path = dataset_manager.get_sensor_data_path(dataset_id, sensor, frame_id)
    if path and os.path.exists(path):
        return FileResponse(path)
    return format_error("Image not found", 1002, {"dataset_id": dataset_id, "frame_id": frame_id, "sensor": sensor})
@router.get("/algorithms")
async def get_algorithms():
    return create_api_response([])
@router.post("/execute")
async def execute_algorithm(request: dict):
    return create_api_response({"status": "started", "execution_id": "test"})
@router.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    return create_api_response({"status": "running", "progress": 0.5})
@router.get("/config")
async def get_config():
    from shared.config import Config
    config = Config()
    config.load("development")
    return create_api_response(config.data)
@router.post("/config/reload")
async def reload_config():
    from shared.config import Config
    config = Config()
    result = config.reload()
    if "error" in result:
        return result
    return create_api_response({"reloaded": True})
@router.post("/config/validate")
async def validate_config():
    from shared.config import Config
    config = Config()
    config.load("development")
    result = config.validate()
    return create_api_response(result)
@router.get("/plugins")
async def get_plugins():
    from shared.config import Config
    from backend.core.plugin_discovery import PluginDiscovery
    config = Config()
    config.load("development")
    discovery = PluginDiscovery(config)
    discovery.scan()
    return create_api_response(discovery.plugins)
@router.post("/plugins/reload")
async def reload_plugins():
    from shared.config import Config
    from backend.core.plugin_discovery import PluginDiscovery
    from backend.core.algorithm_loader import AlgorithmLoader
    config = Config()
    config.load("development")
    discovery = PluginDiscovery(config)
    discovery.scan()
    loader = AlgorithmLoader(discovery)
    result = loader.reload()
    if "error" in result:
        return result
    return create_api_response({"reloaded": True, "plugins": discovery.plugins})
@router.get("/health")
async def health():
    return create_api_response({"status": "healthy"})