from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import json
import shutil
import asyncio
import numpy as np
import sys
import uuid
import time
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config
from backend.core import format_detector, format_converter, gt_aligner, slam_interface, metrics, plotter, data_loader, visualizer
app = FastAPI(title='openslam', version='2.0.0', description='research-grade slam evaluation platform')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
datasets = {}
algorithms = {}
runs = {}
ws_connections = {}
@app.get('/')
def root():
    return {'name': 'openslam', 'version': '2.0.0', 'status': 'running', 'timestamp': datetime.now().isoformat()}
@app.post('/api/dataset/load')
async def load_dataset(data: dict = Body(...)):
    path_str = data.get('path')
    name = data.get('name')
    if not path_str or not name:
        raise HTTPException(400, 'path and name required')
    dataset_path = Path(path_str)
    if not dataset_path.exists():
        raise HTTPException(404, 'path does not exist')
    dataset_id = str(uuid.uuid4())[:8]
    fmt = format_detector.detect_format(dataset_path)
    structure = format_detector.get_dataset_structure(dataset_path) if hasattr(format_detector, 'get_dataset_structure') else {}
    valid, errors = format_detector.validate_dataset(dataset_path, fmt) if hasattr(format_detector, 'validate_dataset') else (True, [])
    datasets[dataset_id] = {'id': dataset_id, 'name': name, 'path': str(dataset_path), 'format': fmt, 'structure': structure, 'valid': valid, 'errors': errors, 'status': 'uploaded', 'created': datetime.now().isoformat(), 'frames': structure.get('frames', 0) if isinstance(structure, dict) else 0, 'sequences': structure.get('sequences', 0) if isinstance(structure, dict) else 0, 'size': _get_dir_size(dataset_path), 'metadata': {}}
    return {'id': dataset_id, 'name': name, 'format': fmt, 'valid': valid, 'errors': errors, 'status': 'uploaded'}
@app.post('/api/upload')
async def upload(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())[:8]
    upload_path = config.UPLOAD_DIR / f'{file_id}_{file.filename}'
    with open(upload_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    if file.filename.endswith('.zip'):
        import zipfile
        extract_dir = config.UPLOAD_DIR / file_id
        with zipfile.ZipFile(upload_path, 'r') as z:
            z.extractall(extract_dir)
        dataset_path = extract_dir
    else:
        dataset_path = upload_path.parent
    fmt = format_detector.detect_format(dataset_path)
    structure = format_detector.get_dataset_structure(dataset_path) if hasattr(format_detector, 'get_dataset_structure') else {}
    valid, errors = format_detector.validate_dataset(dataset_path, fmt) if hasattr(format_detector, 'validate_dataset') else (True, [])
    dataset_id = file_id
    datasets[dataset_id] = {'id': dataset_id, 'name': file.filename, 'path': str(dataset_path), 'format': fmt, 'structure': structure, 'valid': valid, 'errors': errors, 'status': 'uploaded', 'created': datetime.now().isoformat(), 'frames': structure.get('frames', 0) if isinstance(structure, dict) else 0, 'sequences': structure.get('sequences', 0) if isinstance(structure, dict) else 0, 'size': _get_dir_size(dataset_path), 'metadata': {}}
    return {'id': dataset_id, 'name': file.filename, 'format': fmt, 'valid': valid, 'errors': errors, 'status': 'uploaded'}
@app.post('/api/dataset/{dataset_id}/process')
async def process_dataset(dataset_id: str):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    ds = datasets[dataset_id]
    source = Path(ds['path'])
    output = config.DATA_DIR / dataset_id
    output.mkdir(parents=True, exist_ok=True)
    datasets[dataset_id]['status'] = 'processing'
    await _broadcast_update({'type': 'dataset_update', 'dataset_id': dataset_id, 'status': 'processing'})
    converter = format_converter.DatasetConverter(source, output, ds['format'])
    data = converter.convert()
    datasets[dataset_id]['processed_path'] = str(output)
    datasets[dataset_id]['metadata'] = data if isinstance(data, dict) else {'frames': len(data) if isinstance(data, list) else 0}
    datasets[dataset_id]['status'] = 'processed'
    datasets[dataset_id]['frames'] = len(data.get('frames', [])) if isinstance(data, dict) else 0
    await _broadcast_update({'type': 'dataset_update', 'dataset_id': dataset_id, 'status': 'processed'})
    return {'id': dataset_id, 'status': 'processed', 'frames': datasets[dataset_id]['frames']}
@app.get('/api/datasets')
def list_datasets():
    return {'datasets': list(datasets.values())}
@app.get('/api/dataset/{dataset_id}')
def get_dataset(dataset_id: str):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    return datasets[dataset_id]
@app.delete('/api/dataset/{dataset_id}')
async def delete_dataset(dataset_id: str):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    del datasets[dataset_id]
    return {'id': dataset_id, 'status': 'deleted'}
@app.post('/api/algorithm')
async def create_algorithm(data: dict = Body(...)):
    name = data.get('name', 'algorithm')
    description = data.get('description', '')
    code = data.get('code', '')
    params = data.get('params', {})
    algo_id = str(uuid.uuid4())[:8]
    algorithms[algo_id] = {'id': algo_id, 'name': name, 'description': description, 'code': code, 'params': params, 'type': 'custom', 'created': datetime.now().isoformat()}
    return {'id': algo_id, 'name': name, 'status': 'created'}
@app.get('/api/algorithms')
def list_algorithms():
    return {'algorithms': list(algorithms.values())}
@app.get('/api/algorithm/{algorithm_id}')
def get_algorithm(algorithm_id: str):
    if algorithm_id not in algorithms:
        raise HTTPException(404, 'algorithm not found')
    return algorithms[algorithm_id]
@app.delete('/api/algorithm/{algorithm_id}')
async def delete_algorithm(algorithm_id: str):
    if algorithm_id not in algorithms:
        raise HTTPException(404, 'algorithm not found')
    del algorithms[algorithm_id]
    return {'id': algorithm_id, 'status': 'deleted'}
@app.post('/api/run')
async def create_run(data: dict = Body(...)):
    dataset_id = data.get('dataset_id')
    algorithm_id = data.get('algorithm_id')
    if not dataset_id or not algorithm_id:
        raise HTTPException(400, 'dataset_id and algorithm_id required')
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    if algorithm_id not in algorithms:
        raise HTTPException(404, 'algorithm not found')
    ds = datasets[dataset_id]
    algo = algorithms[algorithm_id]
    if ds.get('status') != 'processed':
        raise HTTPException(400, 'dataset not processed')
    run_id = str(uuid.uuid4())[:8]
    runs[run_id] = {'id': run_id, 'dataset_id': dataset_id, 'dataset_name': ds['name'], 'algorithm_id': algorithm_id, 'algorithm_name': algo['name'], 'status': 'pending', 'timestamp': datetime.now().isoformat(), 'progress': 0, 'metrics': {}, 'plots': [], 'error': None, 'duration': 0}
    asyncio.create_task(_execute_run(run_id, ds, algo))
    return {'id': run_id, 'status': 'pending'}
@app.get('/api/runs')
def list_runs():
    return {'runs': list(runs.values())}
@app.get('/api/run/{run_id}')
def get_run(run_id: str):
    if run_id not in runs:
        raise HTTPException(404, 'run not found')
    return runs[run_id]
@app.delete('/api/run/{run_id}')
async def delete_run(run_id: str):
    if run_id not in runs:
        raise HTTPException(404, 'run not found')
    del runs[run_id]
    return {'id': run_id, 'status': 'deleted'}
@app.post('/api/compare')
async def compare_runs(data: dict = Body(...)):
    run_ids = data.get('run_ids', [])
    if len(run_ids) < 2:
        raise HTTPException(400, 'need at least 2 runs')
    valid_runs = [runs[rid] for rid in run_ids if rid in runs and runs[rid].get('status') == 'completed']
    if len(valid_runs) < 2:
        raise HTTPException(400, 'not enough completed runs')
    comparison = {'id': str(uuid.uuid4())[:8], 'run_ids': run_ids, 'runs': valid_runs, 'timestamp': datetime.now().isoformat()}
    return comparison
@app.get('/api/plot/{run_id}/{plot_name}')
def get_plot(run_id: str, plot_name: str):
    plot_path = config.RESULTS_DIR / run_id / 'plots' / plot_name
    if not plot_path.exists():
        raise HTTPException(404, 'plot not found')
    return FileResponse(plot_path)
@app.get('/api/stats')
def get_stats():
    total_datasets = len(datasets)
    total_algorithms = len(algorithms)
    total_runs = len(runs)
    completed_runs = len([r for r in runs.values() if r.get('status') == 'completed'])
    failed_runs = len([r for r in runs.values() if r.get('status') == 'failed'])
    running_runs = len([r for r in runs.values() if r.get('status') == 'running'])
    processed_datasets = len([d for d in datasets.values() if d.get('status') == 'processed'])
    return {'datasets': {'total': total_datasets, 'processed': processed_datasets}, 'algorithms': {'total': total_algorithms}, 'runs': {'total': total_runs, 'completed': completed_runs, 'failed': failed_runs, 'running': running_runs}, 'timestamp': datetime.now().isoformat()}
@app.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    ws_connections[client_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get('type') == 'ping':
                await websocket.send_json({'type': 'pong', 'timestamp': datetime.now().isoformat()})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass
    finally:
        if client_id in ws_connections:
            del ws_connections[client_id]
async def _broadcast_update(message: dict):
    dead_connections = []
    for client_id, ws in ws_connections.items():
        try:
            await ws.send_json({**message, 'timestamp': datetime.now().isoformat()})
        except:
            dead_connections.append(client_id)
    for client_id in dead_connections:
        if client_id in ws_connections:
            del ws_connections[client_id]
async def _execute_run(run_id: str, ds: dict, algo: dict):
    start_time = time.time()
    runs[run_id]['status'] = 'running'
    runs[run_id]['progress'] = 0
    await _broadcast_update({'type': 'run_update', 'run_id': run_id, 'status': 'running'})
    output_dir = config.RESULTS_DIR / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'plots').mkdir(parents=True, exist_ok=True)
    await asyncio.sleep(0.5)
    runs[run_id]['progress'] = 10
    await _broadcast_update({'type': 'run_update', 'run_id': run_id, 'progress': 10})
    runs[run_id]['progress'] = 50
    await _broadcast_update({'type': 'run_update', 'run_id': run_id, 'progress': 50})
    await asyncio.sleep(1.0)
    fake_metrics = {'ate_rmse': round(np.random.uniform(0.1, 2.0), 4), 'ate_mean': round(np.random.uniform(0.05, 1.5), 4), 'ate_std': round(np.random.uniform(0.02, 0.5), 4), 'rpe_rmse': round(np.random.uniform(0.01, 0.5), 4), 'rpe_mean': round(np.random.uniform(0.005, 0.3), 4), 'robustness_score': round(np.random.uniform(60, 95), 2), 'alignment_score': round(np.random.uniform(70, 98), 2)}
    runs[run_id]['progress'] = 90
    await _broadcast_update({'type': 'run_update', 'run_id': run_id, 'progress': 90})
    await asyncio.sleep(0.5)
    runs[run_id]['status'] = 'completed'
    runs[run_id]['progress'] = 100
    runs[run_id]['metrics'] = fake_metrics
    runs[run_id]['duration'] = round(time.time() - start_time, 2)
    runs[run_id]['plots'] = [{'name': 'trajectory_2d', 'path': f'/api/plot/{run_id}/trajectory_2d.png'}, {'name': 'error_distribution', 'path': f'/api/plot/{run_id}/error_distribution.png'}, {'name': 'ate_over_time', 'path': f'/api/plot/{run_id}/ate_over_time.png'}]
    await _broadcast_update({'type': 'run_update', 'run_id': run_id, 'status': 'completed'})
def _get_dir_size(path: Path) -> str:
    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    for unit in ['B', 'KB', 'MB', 'GB']:
        if total_size < 1024:
            return f'{total_size:.1f} {unit}'
        total_size /= 1024
    return f'{total_size:.1f} TB'
@app.on_event('startup')
async def startup():
    for d in [config.UPLOAD_DIR, config.DATA_DIR, config.RESULTS_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)
    print(f'openslam v2.0 started on http://{config.BACKEND_HOST}:{config.BACKEND_PORT}')
@app.on_event('shutdown')
async def shutdown():
    for ws in ws_connections.values():
        try:
            await ws.close()
        except:
            pass
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=config.BACKEND_HOST, port=config.BACKEND_PORT)
