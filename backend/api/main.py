from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import json
import shutil
import asyncio
import numpy as np
import sys
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from backend.core import format_detector, format_converter, gt_aligner, slam_interface, metrics, plotter, data_loader, visualizer

app = FastAPI(title='OpenSLAM', version='2.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

datasets = {}
algorithms = {}
runs = {}
ws_connections = {}

@app.get('/')
def root():
    return {'name': 'OpenSLAM', 'version': '2.0.0', 'status': 'running'}

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
    structure = format_detector.get_dataset_structure(dataset_path)
    valid, errors = format_detector.validate_dataset(dataset_path, fmt)
    dataset_id = file_id
    datasets[dataset_id] = {'id': dataset_id, 'name': file.filename, 'path': str(dataset_path), 'format': fmt, 'structure': structure, 'valid': valid, 'errors': errors, 'status': 'uploaded'}
    return {'id': dataset_id, 'name': file.filename, 'format': fmt, 'valid': valid, 'errors': errors}

@app.post('/api/dataset/{dataset_id}/process')
def process_dataset(dataset_id: str):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    ds = datasets[dataset_id]
    source = Path(ds['path'])
    output = config.DATA_DIR / dataset_id
    converter = format_converter.DatasetConverter(source, output)
    data = converter.convert()
    datasets[dataset_id]['processed_path'] = str(output)
    datasets[dataset_id]['metadata'] = data
    datasets[dataset_id]['status'] = 'processed'
    return {'id': dataset_id, 'status': 'processed', 'frames': len(data.get('frames', []))}

@app.get('/api/datasets')
def list_datasets():
    return {'datasets': list(datasets.values())}

@app.get('/api/dataset/{dataset_id}')
def get_dataset(dataset_id: str):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    return datasets[dataset_id]

@app.post('/api/algorithm')
def create_algorithm(data: dict = Body(...)):
    name = data.get('name', 'algorithm')
    code = data.get('code', '')
    algo_id = str(uuid.uuid4())[:8]
    namespace = {}
    exec(code, namespace)
    algo_class = None
    for item in namespace.values():
        if isinstance(item, type) and issubclass(item, slam_interface.SLAMAlgorithm) and item != slam_interface.SLAMAlgorithm:
            algo_class = item
            break
    if algo_class is None:
        raise HTTPException(400, 'no valid algorithm found')
    algorithms[algo_id] = {'id': algo_id, 'name': name, 'class': algo_class, 'code': code}
    return {'id': algo_id, 'name': name}

@app.get('/api/algorithms')
def list_algorithms():
    return {'algorithms': [{'id': a['id'], 'name': a['name']} for a in algorithms.values()]}

@app.post('/api/run')
async def run(data: dict = Body(...)):
    dataset_id = data.get('dataset_id')
    algorithm_id = data.get('algorithm_id')
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    if algorithm_id not in algorithms:
        raise HTTPException(400, 'algorithm not found')
    ds = datasets[dataset_id]
    algo = algorithms[algorithm_id]
    if ds.get('status') != 'processed':
        raise HTTPException(400, 'dataset not processed')
    run_id = str(uuid.uuid4())[:8]
    runs[run_id] = {'id': run_id, 'dataset_id': dataset_id, 'algorithm_id': algorithm_id, 'status': 'running'}
    asyncio.create_task(execute_run(run_id, ds, algo))
    return {'id': run_id, 'status': 'running'}

async def execute_run(run_id, ds, algo):
    processed_path = ds.get('processed_path')
    dataset = slam_interface.Dataset(processed_path).load()
    algorithm = algo['class']()
    output_dir = config.RESULTS_DIR / run_id
    runner = slam_interface.AlgorithmRunner(algorithm, dataset, output_dir)
    viz = visualizer.LiveVisualizer(output_dir / 'viz')
    gt = dataset.ground_truth
    def on_frame_sync(idx, pose_est, frame_data):
        gt_pose = gt[idx] if gt is not None and idx < len(gt) else None
        viz.add_pose(pose_est.timestamp, pose_est.pose, gt_pose)
        live_data = viz.get_live_data()
        asyncio.create_task(broadcast(run_id, {'type': 'frame', 'data': live_data}))
    result = runner.run(on_frame=on_frame_sync)
    runs[run_id]['status'] = 'completed' if result['success'] else 'failed'
    runs[run_id]['result'] = result
    if result['success'] and gt is not None:
        traj = np.array(result['trajectory'])
        aligned, transform, scale = gt_aligner.align_trajectories(traj, gt)
        quality = gt_aligner.compute_alignment_quality(aligned, gt)
        mets = metrics.compute_all_metrics(aligned, gt)
        mets['robustness'] = metrics.compute_robustness_score(aligned, gt, mets)
        runs[run_id]['metrics'] = mets
        runs[run_id]['alignment'] = {'quality': quality, 'scale': float(scale)}
        plots = plotter.generate_all_plots([aligned], [algo['name']], gt, mets, output_dir / 'plots')
        runs[run_id]['plots'] = plots
    viz.save()
    await broadcast(run_id, {'type': 'complete', 'data': runs[run_id]})

@app.get('/api/run/{run_id}')
def get_run(run_id: str):
    if run_id not in runs:
        raise HTTPException(404, 'run not found')
    return runs[run_id]

@app.get('/api/runs')
def list_runs():
    return {'runs': list(runs.values())}

@app.post('/api/compare')
def compare(data: dict = Body(...)):
    run_ids = data.get('run_ids', [])
    if len(run_ids) < 2:
        raise HTTPException(400, 'need at least 2 runs')
    results = []
    for rid in run_ids:
        if rid not in runs:
            continue
        run = runs[rid]
        if 'result' not in run:
            continue
        algo_name = algorithms[run['algorithm_id']]['name']
        results.append({'label': algo_name, 'trajectory': run['result']['trajectory'], 'metrics': run.get('metrics', {}), 'ground_truth': datasets[run['dataset_id']].get('metadata', {}).get('ground_truth')})
    if len(results) < 2:
        raise HTTPException(400, 'not enough completed runs')
    comp_id = str(uuid.uuid4())[:8]
    output_dir = config.RESULTS_DIR / f'compare_{comp_id}'
    plots = plotter.create_comparison_plots(results, output_dir)
    comparison = {'id': comp_id, 'results': results, 'plots': plots}
    if len(results) == 2:
        comparison['stats'] = metrics.statistical_comparison([results[0]['metrics']], [results[1]['metrics']])
    return comparison

@app.get('/api/plot/{path:path}')
def get_plot(path: str):
    plot_path = config.RESULTS_DIR / path
    if not plot_path.exists():
        raise HTTPException(404, 'plot not found')
    return FileResponse(plot_path)

@app.websocket('/ws/{client_id}')
async def websocket(websocket: WebSocket, client_id: str):
    await websocket.accept()
    ws_connections[client_id] = websocket
    while True:
        try:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})
        except:
            break
    if client_id in ws_connections:
        del ws_connections[client_id]

async def broadcast(run_id, message):
    for ws in ws_connections.values():
        try:
            await ws.send_json({'run_id': run_id, **message})
        except:
            pass

@app.on_event('startup')
def startup():
    for d in [config.UPLOAD_DIR, config.DATA_DIR, config.RESULTS_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=config.BACKEND_HOST, port=config.BACKEND_PORT)
