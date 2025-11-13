from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import json
import shutil
import asyncio
import numpy as np
import sys
import os
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from backend.core import format_detector, format_converter, gt_aligner, slam_interface, metrics, plotter
from backend.core.dataset_manager import DatasetManager
from backend.core.algorithm_loader import AlgorithmLoader
from backend.core.code_executor import CodeExecutor
from backend.core.tutorial_manager import TutorialManager

app = FastAPI(title='OpenSLAM API', version='2.0.0')

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

dataset_manager = DatasetManager()
algorithm_loader = AlgorithmLoader()
code_executor = CodeExecutor()
tutorial_manager = TutorialManager()

active_connections = []
datasets_cache = {}
algorithms_cache = {}
results_cache = {}

class ConnectionManager:
    def __init__(self):
        self.connections = []

    async def connect(self, websocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def send_personal_message(self, message, websocket):
        await websocket.send_text(message)

    async def broadcast(self, message):
        for conn in self.connections:
            await conn.send_text(message)

manager = ConnectionManager()

@app.get('/')
def root():
    return {'status': 'ok', 'version': '2.0.0', 'features': ['auto_detect', 'gt_alignment', 'live_viz', 'multi_algo', 'research']}

@app.post('/api/datasets/upload')
async def upload_dataset(file: UploadFile = File(...)):
    upload_path = config.UPLOAD_DIR / file.filename
    upload_path.parent.mkdir(parents=True, exist_ok=True)

    with open(upload_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)

    if file.filename.endswith('.zip'):
        import zipfile
        extract_path = config.UPLOAD_DIR / file.filename.replace('.zip', '')
        with zipfile.ZipFile(upload_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        dataset_path = extract_path
    else:
        dataset_path = upload_path.parent

    fmt = format_detector.detect_format(dataset_path)
    structure = format_detector.get_dataset_structure(dataset_path)
    valid, errors = format_detector.validate_dataset(dataset_path, fmt)

    dataset_id = file.filename.replace('.zip', '').replace('.', '_')
    datasets_cache[dataset_id] = {'id': dataset_id, 'path': str(dataset_path), 'format': fmt, 'structure': structure, 'valid': valid, 'errors': errors}

    return {'success': True, 'dataset_id': dataset_id, 'format': fmt, 'structure': structure, 'valid': valid, 'errors': errors}

@app.post('/api/browse-directory')
def browse_directory(request: dict):
    path = request.get('path', '/')

    if not os.path.exists(path):
        for fallback in ['/home', '/', '/tmp']:
            if os.path.exists(fallback):
                path = fallback
                break

    items = []

    if path != '/' and path != '':
        parent_path = os.path.dirname(path)
        items.append({'name': '..', 'path': parent_path, 'type': 'directory', 'is_parent': True})

    for item in sorted(os.listdir(path)):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            items.append({'name': item, 'path': item_path, 'type': 'directory', 'is_parent': False})

    return {'current_path': path, 'items': items}

@app.post('/api/datasets/convert')
def convert_dataset(dataset_id: str):
    if dataset_id not in datasets_cache:
        return {'success': False, 'error': 'dataset not found'}

    dataset_info = datasets_cache[dataset_id]
    source_path = Path(dataset_info['path'])
    output_path = config.DATA_DIR / dataset_id / 'converted'

    converter = format_converter.DatasetConverter(source_path, output_path)
    data = converter.convert()

    datasets_cache[dataset_id]['converted_path'] = str(output_path)
    datasets_cache[dataset_id]['metadata'] = data

    return {'success': True, 'output_path': str(output_path), 'metadata': data}

@app.get('/api/datasets')
def list_datasets():
    legacy_datasets = dataset_manager.list_datasets()
    all_datasets = list(datasets_cache.values()) + legacy_datasets
    return {'datasets': all_datasets}

@app.get('/api/datasets/{dataset_id}')
def get_dataset(dataset_id: str):
    if dataset_id in datasets_cache:
        return datasets_cache[dataset_id]
    return dataset_manager.get_dataset(dataset_id)

@app.post('/api/datasets/load')
def load_dataset(request: dict):
    path = request.get('path')
    if not path:
        return {'success': False, 'error': 'path required'}

    dataset = dataset_manager.load_kitti_dataset(path)
    return {'id': dataset.id, 'name': dataset.name, 'format': dataset.format, 'sequence_length': dataset.sequence_length, 'sensors': dataset.sensors}

@app.post('/api/algorithms/register')
def register_algorithm(name: str, code: str, config_params: dict = {}):
    algorithm_id = name.lower().replace(' ', '_')

    namespace = {}
    exec(code, namespace)

    algo_class = None
    for item in namespace.values():
        if isinstance(item, type) and issubclass(item, slam_interface.SLAMAlgorithm) and item != slam_interface.SLAMAlgorithm:
            algo_class = item
            break

    if algo_class is None:
        return {'success': False, 'error': 'no valid SLAM algorithm class found'}

    algorithms_cache[algorithm_id] = {'id': algorithm_id, 'name': name, 'class': algo_class, 'config': config_params}

    return {'success': True, 'algorithm_id': algorithm_id}

@app.get('/api/algorithms')
def list_algorithms():
    return {'algorithms': [{'id': aid, 'name': ainfo['name']} for aid, ainfo in algorithms_cache.items()]}

@app.get('/api/algorithms/library')
def get_algorithm_library():
    algorithms = algorithm_loader.discover_algorithms()
    return algorithms

@app.post('/api/algorithms/{plugin_id}/load')
def load_algorithm_plugin(plugin_id: str):
    algorithm = algorithm_loader.load_algorithm(plugin_id)
    if algorithm is None:
        return {'status': 'error', 'message': 'algorithm not found'}
    return {'status': 'loaded', 'plugin_id': plugin_id}

@app.post('/api/run')
async def run_algorithm(dataset_id: str, algorithm_id: str, websocket_id: str = None):
    if dataset_id not in datasets_cache:
        return {'success': False, 'error': 'dataset not found'}

    if algorithm_id not in algorithms_cache:
        return {'success': False, 'error': 'algorithm not found'}

    dataset_info = datasets_cache[dataset_id]
    algo_info = algorithms_cache[algorithm_id]

    converted_path = dataset_info.get('converted_path')
    if not converted_path:
        return {'success': False, 'error': 'dataset not converted'}

    dataset = slam_interface.Dataset(converted_path).load()
    algorithm = algo_info['class']()

    output_dir = config.RESULTS_DIR / f'{dataset_id}_{algorithm_id}'

    runner = slam_interface.AlgorithmRunner(algorithm, dataset, output_dir)

    async def on_frame(idx, pose_estimate, frame_data):
        if websocket_id:
            await broadcast_to_websocket(websocket_id, {'type': 'frame_update', 'frame_id': idx, 'pose': pose_estimate.to_dict()})

    result = runner.run(on_frame=on_frame if websocket_id else None)

    if result['success'] and dataset.ground_truth is not None:
        trajectory = np.array(result['trajectory'])
        gt = dataset.ground_truth

        aligned, transform, scale = gt_aligner.align_trajectories(trajectory, gt, method='auto')

        quality = gt_aligner.compute_alignment_quality(aligned, gt)

        result['alignment'] = {'transform': transform.tolist(), 'scale': float(scale), 'quality': quality}

        metrics_result = metrics.compute_all_metrics(aligned, gt)
        metrics_result['robustness_score'] = metrics.compute_robustness_score(aligned, gt, metrics_result)

        result['metrics'] = metrics_result

        plots = plotter.generate_all_plots([aligned], [algo_info['name']], gt, metrics_result, output_dir / 'plots')
        result['plots'] = plots

    run_id = f'{dataset_id}_{algorithm_id}'
    results_cache[run_id] = result

    return result

@app.post('/api/compare')
def compare_algorithms(dataset_id: str, algorithm_ids: list):
    if dataset_id not in datasets_cache:
        return {'success': False, 'error': 'dataset not found'}

    results_list = []

    for algo_id in algorithm_ids:
        run_id = f'{dataset_id}_{algo_id}'
        if run_id in results_cache:
            result = results_cache[run_id]
            result['label'] = algorithms_cache[algo_id]['name']
            results_list.append(result)

    if len(results_list) < 2:
        return {'success': False, 'error': 'need at least 2 results to compare'}

    output_dir = config.RESULTS_DIR / f'{dataset_id}_comparison'

    plots = plotter.create_comparison_plots(results_list, output_dir)

    comparison = {'results': results_list, 'plots': plots}

    if len(results_list) == 2:
        comparison['statistical_test'] = metrics.statistical_comparison([results_list[0]['metrics']], [results_list[1]['metrics']])

    return comparison

@app.post('/api/task/evaluate')
def evaluate_task(dataset_id: str, algorithm_id: str, task_type: str = 'navigation'):
    run_id = f'{dataset_id}_{algorithm_id}'

    if run_id not in results_cache:
        return {'success': False, 'error': 'run not found'}

    result = results_cache[run_id]

    if 'trajectory' not in result:
        return {'success': False, 'error': 'no trajectory in result'}

    dataset_info = datasets_cache[dataset_id]
    dataset = slam_interface.Dataset(dataset_info.get('converted_path')).load()

    if dataset.ground_truth is None:
        return {'success': False, 'error': 'no ground truth available'}

    trajectory = np.array(result['trajectory'])
    gt = dataset.ground_truth

    tas = metrics.compute_task_alignment_score(trajectory, gt, task_type)

    requirements = config.TASK_REQUIREMENTS.get(task_type, {})

    evaluation = {'task_type': task_type, 'tas': tas, 'requirements': requirements, 'meets_requirements': tas >= 70}

    return evaluation

@app.get('/api/results/{run_id}')
def get_result(run_id: str):
    if run_id not in results_cache:
        return {'success': False, 'error': 'result not found'}
    return results_cache[run_id]

@app.get('/api/plots/{run_id}/{plot_type}')
def get_plot(run_id: str, plot_type: str):
    if run_id not in results_cache:
        return {'error': 'result not found'}

    result = results_cache[run_id]
    plots = result.get('plots', {})

    if plot_type not in plots:
        return {'error': 'plot not found'}

    plot_path = Path(plots[plot_type])

    if not plot_path.exists():
        return {'error': 'plot file not found'}

    return FileResponse(plot_path)

@app.get('/api/tutorials')
def get_tutorials():
    tutorials = tutorial_manager.get_tutorial_list('default_user')
    return tutorials

@app.get('/api/tutorials/{tutorial_id}')
def get_tutorial(tutorial_id: str):
    result = tutorial_manager.start_tutorial('default_user', tutorial_id)
    return result

@app.get('/api/tutorials/{tutorial_id}/step/{step_index}')
def get_tutorial_step(tutorial_id: str, step_index: int):
    result = tutorial_manager.get_tutorial_step('default_user', tutorial_id, step_index)
    return result

@app.post('/api/tutorials/{tutorial_id}/step/{step_index}/submit')
def submit_tutorial_solution(tutorial_id: str, step_index: int, request: dict):
    code = request.get('code', '')
    execution_result = code_executor.execute_code(code)
    result = tutorial_manager.submit_step_solution('default_user', tutorial_id, step_index, code, {'success': execution_result.success, 'output': execution_result.output, 'error': execution_result.error})
    return result

@app.post('/api/execute-code')
def execute_code_endpoint(request: dict):
    code = request.get('code', '')
    result = code_executor.execute_code(code)
    return {'success': result.success, 'output': result.output, 'error': result.error, 'execution_time': result.execution_time}

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    while True:
        data = await websocket.receive_text()
        message = json.loads(data)
        if message.get('type') == 'ping':
            await manager.send_personal_message(json.dumps({'type': 'pong'}), websocket)

@app.websocket('/ws/{client_id}')
async def websocket_client_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections.append({'id': client_id, 'websocket': websocket})

    while True:
        data = await websocket.receive_text()
        message = json.loads(data)

        if message.get('type') == 'ping':
            await websocket.send_json({'type': 'pong'})

async def broadcast_to_websocket(client_id: str, message: dict):
    for conn in active_connections:
        if conn['id'] == client_id:
            await conn['websocket'].send_json(message)

@app.on_event('startup')
async def startup():
    for d in [config.UPLOAD_DIR, config.DATA_DIR, config.RESULTS_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=config.BACKEND_HOST, port=config.BACKEND_PORT)
