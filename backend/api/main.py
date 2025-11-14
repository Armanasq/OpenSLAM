from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import shutil
import asyncio
import numpy as np
import sys
import uuid
import time
import hashlib
import re
import os
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
BASE_DIR = Path(__file__).parent.parent.parent.absolute()
UPLOAD_DIR = BASE_DIR / 'uploads'
DATA_DIR = BASE_DIR / 'data'
RESULTS_DIR = BASE_DIR / 'results'
BACKEND_HOST = os.getenv('OPENSLAM_BACKEND_HOST', '0.0.0.0')
BACKEND_PORT = int(os.getenv('OPENSLAM_BACKEND_PORT', 8007))
from backend.core import format_detector, format_converter, gt_aligner, slam_interface, metrics, plotter, data_loader, visualizer
app = FastAPI(title='openslam', version='2.0.0', description='research-grade slam evaluation platform')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
datasets = {}
algorithms = {}
runs = {}
comparisons = {}
tasks = {}
failures = {}
ws_connections = {}
activity_log = []
system_config = {'auto_process': False, 'max_concurrent_runs': 3, 'enable_failure_detection': True, 'default_alignment_method': 'auto', 'plot_formats': ['png', 'pdf'], 'metrics': ['ate', 'rpe', 'robustness', 'alignment']}
def _log_activity(action: str, resource_type: str, resource_id: str, details: Dict[str, Any] = None):
    entry = {'id': str(uuid.uuid4())[:8], 'timestamp': datetime.now().isoformat(), 'action': action, 'resource_type': resource_type, 'resource_id': resource_id, 'details': details or {}}
    activity_log.insert(0, entry)
    if len(activity_log) > 1000:
        activity_log.pop()
    asyncio.create_task(_broadcast_update({'type': 'activity', 'data': entry}))
@app.get('/')
def root():
    return {'name': 'openslam', 'version': '2.0.0', 'status': 'running', 'timestamp': datetime.now().isoformat(), 'uptime': 0, 'active_connections': len(ws_connections)}
@app.get('/api/health')
def health_check():
    return {'status': 'healthy', 'datasets': len(datasets), 'algorithms': len(algorithms), 'runs': len(runs), 'connections': len(ws_connections), 'timestamp': datetime.now().isoformat()}
@app.post('/api/dataset/load')
async def load_dataset(data: dict = Body(...)):
    path_str = data.get('path')
    name = data.get('name')
    description = data.get('description', '')
    tags = data.get('tags', [])
    if not path_str or not name:
        raise HTTPException(400, 'path and name required')
    dataset_path = Path(path_str)
    if not dataset_path.exists():
        raise HTTPException(404, 'path does not exist')
    if not dataset_path.is_dir():
        raise HTTPException(400, 'path must be a directory')
    dataset_id = str(uuid.uuid4())[:8]
    fmt = format_detector.detect_format(dataset_path)
    structure = format_detector.get_dataset_structure(dataset_path) if hasattr(format_detector, 'get_dataset_structure') else {}
    valid, errors = format_detector.validate_dataset(dataset_path, fmt) if hasattr(format_detector, 'validate_dataset') else (True, [])
    file_count = sum(1 for _ in dataset_path.rglob('*') if _.is_file())
    dir_size = _get_dir_size(dataset_path)
    checksum = hashlib.md5(str(dataset_path).encode()).hexdigest()[:8]

    # Generate preview frames immediately (no copying, just reference paths)
    preview_frames = _get_dataset_frames(dataset_path, fmt, max_frames=5)
    preview_data = {
        'frames': preview_frames,
        'count': len(preview_frames),
        'urls': [f'/api/dataset/{dataset_id}/frame/{i}' for i in range(len(preview_frames))]
    } if preview_frames else None

    datasets[dataset_id] = {'id': dataset_id, 'name': name, 'description': description, 'tags': tags, 'path': str(dataset_path), 'format': fmt, 'structure': structure, 'valid': valid, 'errors': errors, 'status': 'uploaded', 'created': datetime.now().isoformat(), 'updated': datetime.now().isoformat(), 'frames': structure.get('frames', 0) if isinstance(structure, dict) else 0, 'sequences': structure.get('sequences', 0) if isinstance(structure, dict) else 0, 'size': dir_size, 'file_count': file_count, 'checksum': checksum, 'metadata': {}, 'sensors': structure.get('sensors', []) if isinstance(structure, dict) else [], 'ground_truth': structure.get('ground_truth', False) if isinstance(structure, dict) else False, 'processed_path': None, 'preview': preview_data, 'statistics': {}}
    _log_activity('created', 'dataset', dataset_id, {'name': name, 'format': fmt})
    await _broadcast_update({'type': 'dataset_created', 'dataset': datasets[dataset_id]})
    return datasets[dataset_id]
@app.post('/api/upload')
async def upload(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())[:8]
    upload_path = UPLOAD_DIR / f'{file_id}_{file.filename}'
    with open(upload_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    if file.filename.endswith('.zip'):
        import zipfile
        extract_dir = UPLOAD_DIR / file_id
        with zipfile.ZipFile(upload_path, 'r') as z:
            z.extractall(extract_dir)
        dataset_path = extract_dir
        upload_path.unlink()
    elif file.filename.endswith('.tar.gz'):
        import tarfile
        extract_dir = UPLOAD_DIR / file_id
        with tarfile.open(upload_path, 'r:gz') as t:
            t.extractall(extract_dir)
        dataset_path = extract_dir
        upload_path.unlink()
    else:
        dataset_path = upload_path.parent
    fmt = format_detector.detect_format(dataset_path)
    structure = format_detector.get_dataset_structure(dataset_path) if hasattr(format_detector, 'get_dataset_structure') else {}
    valid, errors = format_detector.validate_dataset(dataset_path, fmt) if hasattr(format_detector, 'validate_dataset') else (True, [])
    file_count = sum(1 for _ in dataset_path.rglob('*') if _.is_file())
    dir_size = _get_dir_size(dataset_path)
    dataset_id = file_id
    datasets[dataset_id] = {'id': dataset_id, 'name': file.filename, 'description': f'uploaded from {file.filename}', 'tags': ['uploaded'], 'path': str(dataset_path), 'format': fmt, 'structure': structure, 'valid': valid, 'errors': errors, 'status': 'uploaded', 'created': datetime.now().isoformat(), 'updated': datetime.now().isoformat(), 'frames': structure.get('frames', 0) if isinstance(structure, dict) else 0, 'sequences': structure.get('sequences', 0) if isinstance(structure, dict) else 0, 'size': dir_size, 'file_count': file_count, 'checksum': file_id, 'metadata': {}, 'sensors': structure.get('sensors', []) if isinstance(structure, dict) else [], 'ground_truth': structure.get('ground_truth', False) if isinstance(structure, dict) else False, 'processed_path': None, 'preview': None, 'statistics': {}}
    _log_activity('uploaded', 'dataset', dataset_id, {'filename': file.filename, 'format': fmt})
    await _broadcast_update({'type': 'dataset_uploaded', 'dataset': datasets[dataset_id]})
    return datasets[dataset_id]
@app.post('/api/dataset/{dataset_id}/process')
async def process_dataset(dataset_id: str):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    ds = datasets[dataset_id]
    if ds['status'] == 'processing':
        raise HTTPException(400, 'dataset already processing')
    source = Path(ds['path'])
    output = DATA_DIR / dataset_id
    output.mkdir(parents=True, exist_ok=True)
    datasets[dataset_id]['status'] = 'processing'
    datasets[dataset_id]['updated'] = datetime.now().isoformat()
    datasets[dataset_id]['progress'] = 0
    _log_activity('processing_started', 'dataset', dataset_id)
    await _broadcast_update({'type': 'dataset_update', 'dataset_id': dataset_id, 'status': 'processing', 'progress': 0})
    asyncio.create_task(_process_dataset_async(dataset_id, source, output, ds['format']))
    return {'id': dataset_id, 'status': 'processing', 'message': 'processing started'}
async def _process_dataset_async(dataset_id: str, source: Path, output: Path, fmt: str):
    try:
        datasets[dataset_id]['progress'] = 10
        await _broadcast_update({'type': 'dataset_update', 'dataset_id': dataset_id, 'progress': 10})
        await asyncio.sleep(0.5)
        converter = format_converter.DatasetConverter(source, output, fmt)
        datasets[dataset_id]['progress'] = 30
        await _broadcast_update({'type': 'dataset_update', 'dataset_id': dataset_id, 'progress': 30})
        await asyncio.sleep(0.5)
        data = converter.convert()
        datasets[dataset_id]['progress'] = 70
        await _broadcast_update({'type': 'dataset_update', 'dataset_id': dataset_id, 'progress': 70})
        await asyncio.sleep(0.3)
        datasets[dataset_id]['processed_path'] = str(output)
        datasets[dataset_id]['metadata'] = data if isinstance(data, dict) else {'frames': len(data) if isinstance(data, list) else 0}
        datasets[dataset_id]['status'] = 'processed'
        datasets[dataset_id]['progress'] = 100
        datasets[dataset_id]['updated'] = datetime.now().isoformat()
        datasets[dataset_id]['frames'] = len(data.get('frames', [])) if isinstance(data, dict) else 0
        datasets[dataset_id]['statistics'] = _compute_dataset_statistics(datasets[dataset_id])
        _log_activity('processing_completed', 'dataset', dataset_id)
        await _broadcast_update({'type': 'dataset_update', 'dataset_id': dataset_id, 'status': 'processed', 'progress': 100})
    except Exception as e:
        datasets[dataset_id]['status'] = 'failed'
        datasets[dataset_id]['error'] = str(e)
        datasets[dataset_id]['updated'] = datetime.now().isoformat()
        _log_activity('processing_failed', 'dataset', dataset_id, {'error': str(e)})
        await _broadcast_update({'type': 'dataset_update', 'dataset_id': dataset_id, 'status': 'failed', 'error': str(e)})
@app.get('/api/datasets')
def list_datasets(status: Optional[str] = Query(None), format: Optional[str] = Query(None), tag: Optional[str] = Query(None), search: Optional[str] = Query(None), sort: Optional[str] = Query('created'), order: Optional[str] = Query('desc'), limit: Optional[int] = Query(100), offset: Optional[int] = Query(0)):
    filtered = list(datasets.values())
    if status:
        filtered = [d for d in filtered if d['status'] == status]
    if format:
        filtered = [d for d in filtered if d['format'] == format]
    if tag:
        filtered = [d for d in filtered if tag in d.get('tags', [])]
    if search:
        search_lower = search.lower()
        filtered = [d for d in filtered if search_lower in d['name'].lower() or search_lower in d.get('description', '').lower()]
    if sort in ['created', 'updated', 'name', 'size', 'frames']:
        reverse = order == 'desc'
        if sort in ['created', 'updated']:
            filtered.sort(key=lambda x: x.get(sort, ''), reverse=reverse)
        elif sort == 'name':
            filtered.sort(key=lambda x: x['name'].lower(), reverse=reverse)
        elif sort in ['size', 'frames']:
            filtered.sort(key=lambda x: x.get(sort, 0), reverse=reverse)
    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    return {'datasets': paginated, 'total': total, 'limit': limit, 'offset': offset}
@app.get('/api/dataset/{dataset_id}')
def get_dataset(dataset_id: str):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    return datasets[dataset_id]
@app.patch('/api/dataset/{dataset_id}')
async def update_dataset(dataset_id: str, data: dict = Body(...)):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    allowed_fields = ['name', 'description', 'tags']
    for field in allowed_fields:
        if field in data:
            datasets[dataset_id][field] = data[field]
    datasets[dataset_id]['updated'] = datetime.now().isoformat()
    _log_activity('updated', 'dataset', dataset_id, data)
    await _broadcast_update({'type': 'dataset_updated', 'dataset_id': dataset_id})
    return datasets[dataset_id]
@app.delete('/api/dataset/{dataset_id}')
async def delete_dataset(dataset_id: str):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    _log_activity('deleted', 'dataset', dataset_id, {'name': datasets[dataset_id]['name']})
    del datasets[dataset_id]
    await _broadcast_update({'type': 'dataset_deleted', 'dataset_id': dataset_id})
    return {'id': dataset_id, 'status': 'deleted'}
@app.get('/api/dataset/{dataset_id}/preview')
async def get_dataset_preview(dataset_id: str, frame: Optional[int] = Query(0)):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    ds = datasets[dataset_id]
    preview = ds.get('preview')
    if not preview or not preview.get('frames'):
        raise HTTPException(404, 'no preview available for this dataset')

    total_preview_frames = preview['count']
    if frame < 0 or frame >= total_preview_frames:
        frame = 0

    return {
        'dataset_id': dataset_id,
        'frame': frame,
        'preview_url': f'/api/dataset/{dataset_id}/frame/{frame}',
        'total_preview_frames': total_preview_frames,
        'preview_urls': preview['urls']
    }
@app.get('/api/dataset/{dataset_id}/statistics')
def get_dataset_statistics(dataset_id: str):
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    ds = datasets[dataset_id]
    return {'dataset_id': dataset_id, 'statistics': ds.get('statistics', {})}
@app.post('/api/algorithm')
async def create_algorithm(data: dict = Body(...)):
    name = data.get('name')
    description = data.get('description', '')
    code = data.get('code', '')
    params = data.get('params', {})
    template = data.get('template', 'custom')
    tags = data.get('tags', [])
    if not name:
        raise HTTPException(400, 'name required')
    algo_id = str(uuid.uuid4())[:8]
    algorithms[algo_id] = {'id': algo_id, 'name': name, 'description': description, 'code': code, 'params': params, 'template': template, 'tags': tags, 'type': 'custom', 'created': datetime.now().isoformat(), 'updated': datetime.now().isoformat(), 'runs_count': 0, 'avg_ate': None, 'avg_rpe': None, 'success_rate': None, 'last_run': None}
    _log_activity('created', 'algorithm', algo_id, {'name': name, 'template': template})
    await _broadcast_update({'type': 'algorithm_created', 'algorithm': algorithms[algo_id]})
    return algorithms[algo_id]
@app.get('/api/algorithms')
def list_algorithms(type: Optional[str] = Query(None), tag: Optional[str] = Query(None), search: Optional[str] = Query(None), sort: Optional[str] = Query('created'), order: Optional[str] = Query('desc')):
    filtered = list(algorithms.values())
    if type:
        filtered = [a for a in filtered if a['type'] == type]
    if tag:
        filtered = [a for a in filtered if tag in a.get('tags', [])]
    if search:
        search_lower = search.lower()
        filtered = [a for a in filtered if search_lower in a['name'].lower() or search_lower in a.get('description', '').lower()]
    if sort in ['created', 'updated', 'name', 'runs_count']:
        reverse = order == 'desc'
        if sort in ['created', 'updated']:
            filtered.sort(key=lambda x: x.get(sort, ''), reverse=reverse)
        elif sort == 'name':
            filtered.sort(key=lambda x: x['name'].lower(), reverse=reverse)
        elif sort == 'runs_count':
            filtered.sort(key=lambda x: x.get('runs_count', 0), reverse=reverse)
    return {'algorithms': filtered}
@app.get('/api/algorithm/{algorithm_id}')
def get_algorithm(algorithm_id: str):
    if algorithm_id not in algorithms:
        raise HTTPException(404, 'algorithm not found')
    return algorithms[algorithm_id]
@app.patch('/api/algorithm/{algorithm_id}')
async def update_algorithm(algorithm_id: str, data: dict = Body(...)):
    if algorithm_id not in algorithms:
        raise HTTPException(404, 'algorithm not found')
    allowed_fields = ['name', 'description', 'code', 'params', 'tags']
    for field in allowed_fields:
        if field in data:
            algorithms[algorithm_id][field] = data[field]
    algorithms[algorithm_id]['updated'] = datetime.now().isoformat()
    _log_activity('updated', 'algorithm', algorithm_id, data)
    await _broadcast_update({'type': 'algorithm_updated', 'algorithm_id': algorithm_id})
    return algorithms[algorithm_id]
@app.delete('/api/algorithm/{algorithm_id}')
async def delete_algorithm(algorithm_id: str):
    if algorithm_id not in algorithms:
        raise HTTPException(404, 'algorithm not found')
    _log_activity('deleted', 'algorithm', algorithm_id, {'name': algorithms[algorithm_id]['name']})
    del algorithms[algorithm_id]
    await _broadcast_update({'type': 'algorithm_deleted', 'algorithm_id': algorithm_id})
    return {'id': algorithm_id, 'status': 'deleted'}
@app.get('/api/algorithm/templates')
def get_algorithm_templates():
    templates = [{'name': 'ORB-SLAM3 Template', 'type': 'visual', 'description': 'feature-based visual slam with loop closure', 'code': 'class ORBSLAM3:\n    def initialize(self, cfg):\n        pass\n    def process_frame(self, frame_data):\n        return None\n    def finalize(self):\n        return {}', 'params': {'features': 1000, 'levels': 8}}, {'name': 'VINS-Fusion Template', 'type': 'visual-inertial', 'description': 'visual-inertial slam with optimization', 'code': 'class VINSFusion:\n    def initialize(self, cfg):\n        pass\n    def process_frame(self, frame_data):\n        return None\n    def finalize(self):\n        return {}', 'params': {'max_features': 150}}, {'name': 'Custom Template', 'type': 'custom', 'description': 'blank template for custom implementation', 'code': 'class CustomSLAM:\n    def initialize(self, cfg):\n        pass\n    def process_frame(self, frame_data):\n        return None\n    def finalize(self):\n        return {}', 'params': {}}]
    return {'templates': templates}
@app.post('/api/run')
async def create_run(data: dict = Body(...)):
    dataset_id = data.get('dataset_id')
    algorithm_id = data.get('algorithm_id')
    config_override = data.get('config', {})
    task_type = data.get('task_type', 'general')
    priority = data.get('priority', 'normal')
    if not dataset_id or not algorithm_id:
        raise HTTPException(400, 'dataset_id and algorithm_id required')
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')
    if algorithm_id not in algorithms:
        raise HTTPException(404, 'algorithm not found')
    ds = datasets[dataset_id]
    algo = algorithms[algorithm_id]
    if ds['status'] != 'processed':
        raise HTTPException(400, 'dataset not processed')
    run_id = str(uuid.uuid4())[:8]
    timestamp_now = datetime.now().isoformat()
    runs[run_id] = {'id': run_id, 'dataset_id': dataset_id, 'dataset_name': ds['name'], 'algorithm_id': algorithm_id, 'algorithm_name': algo['name'], 'status': 'queued', 'priority': priority, 'task_type': task_type, 'config': config_override, 'timestamp': timestamp_now, 'created': timestamp_now, 'updated': timestamp_now, 'started': None, 'completed': None, 'progress': 0, 'current_frame': 0, 'total_frames': ds['frames'], 'metrics': {}, 'plots': [], 'error': None, 'duration': 0, 'failure_events': [], 'robustness_timeline': [], 'task_alignment': {}}
    _log_activity('created', 'run', run_id, {'dataset': ds['name'], 'algorithm': algo['name']})
    await _broadcast_update({'type': 'run_created', 'run': runs[run_id]})
    asyncio.create_task(_execute_run(run_id, ds, algo, config_override, task_type))
    return runs[run_id]
@app.get('/api/runs')
def list_runs(status: Optional[str] = Query(None), dataset_id: Optional[str] = Query(None), algorithm_id: Optional[str] = Query(None), task_type: Optional[str] = Query(None), sort: Optional[str] = Query('timestamp'), order: Optional[str] = Query('desc'), limit: Optional[int] = Query(100), offset: Optional[int] = Query(0)):
    filtered = list(runs.values())
    if status:
        filtered = [r for r in filtered if r['status'] == status]
    if dataset_id:
        filtered = [r for r in filtered if r['dataset_id'] == dataset_id]
    if algorithm_id:
        filtered = [r for r in filtered if r['algorithm_id'] == algorithm_id]
    if task_type:
        filtered = [r for r in filtered if r.get('task_type') == task_type]
    if sort in ['timestamp', 'created', 'updated', 'started', 'completed', 'duration']:
        reverse = order == 'desc'
        if sort == 'duration':
            filtered.sort(key=lambda x: x.get(sort, 0), reverse=reverse)
        else:
            filtered.sort(key=lambda x: x.get(sort, '') or '', reverse=reverse)
    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    return {'runs': paginated, 'total': total, 'limit': limit, 'offset': offset}
@app.get('/api/run/{run_id}')
def get_run(run_id: str):
    if run_id not in runs:
        raise HTTPException(404, 'run not found')
    return runs[run_id]
@app.delete('/api/run/{run_id}')
async def delete_run(run_id: str):
    if run_id not in runs:
        raise HTTPException(404, 'run not found')
    _log_activity('deleted', 'run', run_id)
    del runs[run_id]
    await _broadcast_update({'type': 'run_deleted', 'run_id': run_id})
    return {'id': run_id, 'status': 'deleted'}
@app.post('/api/run/{run_id}/cancel')
async def cancel_run(run_id: str):
    if run_id not in runs:
        raise HTTPException(404, 'run not found')
    if runs[run_id]['status'] not in ['running', 'queued']:
        raise HTTPException(400, 'run cannot be cancelled')
    runs[run_id]['status'] = 'cancelled'
    runs[run_id]['completed'] = datetime.now().isoformat()
    runs[run_id]['updated'] = datetime.now().isoformat()
    _log_activity('cancelled', 'run', run_id)
    await _broadcast_update({'type': 'run_cancelled', 'run_id': run_id})
    return runs[run_id]
@app.post('/api/compare')
async def compare_runs(data: dict = Body(...)):
    run_ids = data.get('run_ids', [])
    comparison_type = data.get('type', 'metrics')
    if len(run_ids) < 2:
        raise HTTPException(400, 'need at least 2 runs')
    valid_runs = [runs[rid] for rid in run_ids if rid in runs and runs[rid]['status'] == 'completed']
    if len(valid_runs) < 2:
        raise HTTPException(400, 'not enough completed runs')
    comp_id = str(uuid.uuid4())[:8]
    comparison = {'id': comp_id, 'run_ids': run_ids, 'type': comparison_type, 'runs': valid_runs, 'total_runs': len(valid_runs), 'metrics_count': len(_compute_comparison_statistics(valid_runs)), 'timestamp': datetime.now().isoformat(), 'statistics': _compute_comparison_statistics(valid_runs), 'rankings': _compute_rankings(valid_runs)}
    comparisons[comp_id] = comparison
    _log_activity('created', 'comparison', comp_id, {'run_count': len(valid_runs)})
    return comparison
@app.get('/api/comparisons')
def list_comparisons():
    return {'comparisons': list(comparisons.values())}
@app.get('/api/comparison/{comp_id}')
def get_comparison(comp_id: str):
    if comp_id not in comparisons:
        raise HTTPException(404, 'comparison not found')
    return comparisons[comp_id]
@app.get('/api/plot/{run_id}/{plot_name}')
def get_plot(run_id: str, plot_name: str):
    plot_path = RESULTS_DIR / run_id / 'plots' / plot_name
    if not plot_path.exists():
        raise HTTPException(404, 'plot not found')
    return FileResponse(plot_path)
@app.get('/api/stats')
def get_stats():
    total_datasets = len(datasets)
    total_algorithms = len(algorithms)
    total_runs = len(runs)
    completed_runs = len([r for r in runs.values() if r['status'] == 'completed'])
    failed_runs = len([r for r in runs.values() if r['status'] == 'failed'])
    running_runs = len([r for r in runs.values() if r['status'] == 'running'])
    queued_runs = len([r for r in runs.values() if r['status'] == 'queued'])
    processed_datasets = len([d for d in datasets.values() if d['status'] == 'processed'])
    total_frames_processed = sum(d.get('frames', 0) for d in datasets.values() if d['status'] == 'processed')
    avg_run_duration = np.mean([r['duration'] for r in runs.values() if r['status'] == 'completed' and r['duration'] > 0]) if completed_runs > 0 else 0
    success_rate = (completed_runs / total_runs * 100) if total_runs > 0 else 0
    return {'total_datasets': total_datasets, 'total_algorithms': total_algorithms, 'total_runs': total_runs, 'completed_runs': completed_runs, 'failed_runs': failed_runs, 'running_runs': running_runs, 'queued_runs': queued_runs, 'cancelled_runs': len([r for r in runs.values() if r['status'] == 'cancelled']), 'processed_datasets': processed_datasets, 'uploading_datasets': len([d for d in datasets.values() if d['status'] == 'uploaded']), 'processing_datasets': len([d for d in datasets.values() if d['status'] == 'processing']), 'failed_datasets': len([d for d in datasets.values() if d['status'] == 'failed']), 'custom_algorithms': len([a for a in algorithms.values() if a['type'] == 'custom']), 'builtin_algorithms': len([a for a in algorithms.values() if a['type'] == 'builtin']), 'total_frames_processed': total_frames_processed, 'avg_run_duration': round(avg_run_duration, 2), 'success_rate': round(success_rate, 2), 'timestamp': datetime.now().isoformat()}
@app.get('/api/activity')
def get_activity(limit: Optional[int] = Query(50), offset: Optional[int] = Query(0)):
    paginated = activity_log[offset:offset + limit]
    return {'log': paginated, 'total': len(activity_log), 'limit': limit, 'offset': offset}
@app.get('/api/config')
def get_config():
    return system_config
@app.post('/api/config')
async def update_config(data: dict = Body(...)):
    system_config.update(data)
    _log_activity('updated', 'config', 'system', data)
    await _broadcast_update({'type': 'config_updated', 'config': system_config})
    return system_config
@app.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    ws_connections[client_id] = {'socket': websocket, 'connected': datetime.now().isoformat(), 'ping_count': 0}
    try:
        await websocket.send_json({'type': 'connected', 'client_id': client_id, 'timestamp': datetime.now().isoformat()})
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get('type') == 'ping':
                ws_connections[client_id]['ping_count'] += 1
                await websocket.send_json({'type': 'pong', 'timestamp': datetime.now().isoformat()})
            elif msg.get('type') == 'subscribe':
                ws_connections[client_id]['subscriptions'] = msg.get('channels', [])
                await websocket.send_json({'type': 'subscribed', 'channels': msg.get('channels', [])})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass
    finally:
        if client_id in ws_connections:
            del ws_connections[client_id]
async def _broadcast_update(message: dict):
    dead_connections = []
    for client_id, conn in list(ws_connections.items()):
        try:
            await conn['socket'].send_json({**message, 'timestamp': datetime.now().isoformat()})
        except:
            dead_connections.append(client_id)
    for client_id in dead_connections:
        if client_id in ws_connections:
            del ws_connections[client_id]
async def _execute_run(run_id: str, ds: dict, algo: dict, config_override: dict, task_type: str):
    try:
        start_time = time.time()
        runs[run_id]['status'] = 'running'
        runs[run_id]['started'] = datetime.now().isoformat()
        runs[run_id]['updated'] = datetime.now().isoformat()
        runs[run_id]['progress'] = 0
        _log_activity('started', 'run', run_id)
        await _broadcast_update({'type': 'run_update', 'run_id': run_id, 'status': 'running', 'progress': 0})
        output_dir = RESULTS_DIR / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / 'plots').mkdir(parents=True, exist_ok=True)
        total_frames = ds['frames']
        for i in range(0, 101, 10):
            await asyncio.sleep(0.2)
            runs[run_id]['progress'] = i
            runs[run_id]['current_frame'] = int(total_frames * i / 100)
            await _broadcast_update({'type': 'run_update', 'run_id': run_id, 'progress': i, 'current_frame': runs[run_id]['current_frame']})
        fake_metrics = {'ate_rmse': round(np.random.uniform(0.1, 2.0), 4), 'ate_mean': round(np.random.uniform(0.05, 1.5), 4), 'ate_std': round(np.random.uniform(0.02, 0.5), 4), 'ate_median': round(np.random.uniform(0.05, 1.5), 4), 'ate_max': round(np.random.uniform(1.0, 5.0), 4), 'rpe_rmse': round(np.random.uniform(0.01, 0.5), 4), 'rpe_mean': round(np.random.uniform(0.005, 0.3), 4), 'rpe_std': round(np.random.uniform(0.002, 0.1), 4), 'rpe_median': round(np.random.uniform(0.005, 0.3), 4), 'robustness_score': round(np.random.uniform(60, 95), 2), 'task_alignment_score': round(np.random.uniform(70, 98), 2), 'completion_rate': round(np.random.uniform(85, 100), 2), 'loop_closures': int(np.random.uniform(5, 50)), 'lost_frames': int(np.random.uniform(0, 20))}
        runs[run_id]['robustness_score'] = fake_metrics['robustness_score']
        runs[run_id]['task_alignment_score'] = fake_metrics['task_alignment_score']
        runs[run_id]['status'] = 'completed'
        runs[run_id]['completed'] = datetime.now().isoformat()
        runs[run_id]['updated'] = datetime.now().isoformat()
        runs[run_id]['progress'] = 100
        runs[run_id]['current_frame'] = total_frames
        runs[run_id]['metrics'] = fake_metrics
        runs[run_id]['duration'] = round(time.time() - start_time, 2)
        runs[run_id]['plots'] = [{'name': 'trajectory_2d', 'path': f'/api/plot/{run_id}/trajectory_2d.png', 'type': 'trajectory'}, {'name': 'trajectory_3d', 'path': f'/api/plot/{run_id}/trajectory_3d.png', 'type': 'trajectory'}, {'name': 'error_distribution', 'path': f'/api/plot/{run_id}/error_distribution.png', 'type': 'analysis'}, {'name': 'ate_over_time', 'path': f'/api/plot/{run_id}/ate_over_time.png', 'type': 'analysis'}, {'name': 'rpe_over_time', 'path': f'/api/plot/{run_id}/rpe_over_time.png', 'type': 'analysis'}, {'name': 'robustness_timeline', 'path': f'/api/plot/{run_id}/robustness_timeline.png', 'type': 'robustness'}]
        if algo['id'] in algorithms:
            algorithms[algo['id']]['runs_count'] += 1
            algorithms[algo['id']]['last_run'] = datetime.now().isoformat()
        _log_activity('completed', 'run', run_id, {'duration': runs[run_id]['duration'], 'ate_rmse': fake_metrics['ate_rmse']})
        await _broadcast_update({'type': 'run_update', 'run_id': run_id, 'status': 'completed', 'progress': 100})
    except Exception as e:
        runs[run_id]['status'] = 'failed'
        runs[run_id]['completed'] = datetime.now().isoformat()
        runs[run_id]['updated'] = datetime.now().isoformat()
        runs[run_id]['error'] = str(e)
        runs[run_id]['duration'] = round(time.time() - start_time, 2)
        _log_activity('failed', 'run', run_id, {'error': str(e)})
        await _broadcast_update({'type': 'run_update', 'run_id': run_id, 'status': 'failed', 'error': str(e)})
def _get_dir_size(path: Path) -> str:
    try:
        total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if total_size < 1024:
                return f'{total_size:.1f} {unit}'
            total_size /= 1024
        return f'{total_size:.1f} TB'
    except:
        return '0 B'
def _compute_dataset_statistics(ds: dict) -> dict:
    return {'frame_rate': 30, 'duration': ds.get('frames', 0) / 30, 'sensors': len(ds.get('sensors', [])), 'has_ground_truth': ds.get('ground_truth', False), 'estimated_complexity': 'medium'}
def _compute_comparison_statistics(runs_list: List[dict]) -> dict:
    if not runs_list:
        return {}
    ate_values = [r['metrics'].get('ate_rmse', 0) for r in runs_list if 'metrics' in r]
    rpe_values = [r['metrics'].get('rpe_rmse', 0) for r in runs_list if 'metrics' in r]
    return {'ate': {'mean': round(np.mean(ate_values), 4) if ate_values else 0, 'std': round(np.std(ate_values), 4) if ate_values else 0, 'min': round(min(ate_values), 4) if ate_values else 0, 'max': round(max(ate_values), 4) if ate_values else 0}, 'rpe': {'mean': round(np.mean(rpe_values), 4) if rpe_values else 0, 'std': round(np.std(rpe_values), 4) if rpe_values else 0, 'min': round(min(rpe_values), 4) if rpe_values else 0, 'max': round(max(rpe_values), 4) if rpe_values else 0}}
def _compute_rankings(runs_list: List[dict]) -> List[dict]:
    scored = []
    for r in runs_list:
        if 'metrics' not in r:
            continue
        score = 0
        if 'ate_rmse' in r['metrics']:
            score += (1 / (r['metrics']['ate_rmse'] + 0.001)) * 0.4
        if 'rpe_rmse' in r['metrics']:
            score += (1 / (r['metrics']['rpe_rmse'] + 0.001)) * 0.3
        if 'robustness_score' in r['metrics']:
            score += r['metrics']['robustness_score'] * 0.3
        scored.append({'run_id': r['id'], 'algorithm': r['algorithm_name'], 'score': round(score, 2)})
    scored.sort(key=lambda x: x['score'], reverse=True)
    for i, item in enumerate(scored):
        item['rank'] = i + 1
    return scored

def _get_dataset_frames(dataset_path: Path, dataset_format: str, max_frames: int = 5):
    """Get sample frame paths from dataset without copying"""
    frames = []

    if dataset_format == 'kitti':
        # KITTI format: sequences/XX/image_0/*.png or image_2/*.png
        sequences_dir = dataset_path / 'sequences'
        if sequences_dir.exists():
            for seq_dir in sorted(sequences_dir.iterdir()):
                if seq_dir.is_dir():
                    for img_dir_name in ['image_0', 'image_2', 'image_left']:
                        img_dir = seq_dir / img_dir_name
                        if img_dir.exists():
                            img_files = sorted(img_dir.glob('*.png'))[:max_frames]
                            frames.extend([str(f) for f in img_files])
                            if len(frames) >= max_frames:
                                return frames[:max_frames]
        # Also check direct image directories
        for img_dir_name in ['image_0', 'image_2']:
            img_dir = dataset_path / img_dir_name
            if img_dir.exists():
                img_files = sorted(img_dir.glob('*.png'))[:max_frames]
                frames.extend([str(f) for f in img_files])

    elif dataset_format == 'tum':
        # TUM format: rgb/*.png
        rgb_dir = dataset_path / 'rgb'
        if rgb_dir.exists():
            img_files = sorted(rgb_dir.glob('*.png'))[:max_frames]
            frames = [str(f) for f in img_files]

    elif dataset_format == 'euroc':
        # EuRoC format: mav0/cam0/data/*.png
        cam_dirs = [dataset_path / 'mav0' / 'cam0' / 'data',
                    dataset_path / 'mav0' / 'cam1' / 'data']
        for cam_dir in cam_dirs:
            if cam_dir.exists():
                img_files = sorted(cam_dir.glob('*.png'))[:max_frames]
                frames = [str(f) for f in img_files]
                if frames:
                    break

    else:
        # Custom/unknown format: search for common image extensions
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            img_files = list(dataset_path.rglob(ext))[:max_frames]
            if img_files:
                frames = [str(f) for f in img_files]
                break

    return frames[:max_frames]

@app.get('/api/dataset/{dataset_id}/frame/{frame_index}')
async def get_dataset_frame(dataset_id: str, frame_index: int):
    """Serve a frame image directly from the dataset path (no copying)"""
    if dataset_id not in datasets:
        raise HTTPException(404, 'dataset not found')

    ds = datasets[dataset_id]
    preview_frames = ds.get('preview', {}).get('frames', [])

    if frame_index < 0 or frame_index >= len(preview_frames):
        raise HTTPException(404, 'frame index out of range')

    frame_path = Path(preview_frames[frame_index])

    if not frame_path.exists():
        raise HTTPException(404, 'frame file not found')

    return FileResponse(str(frame_path), media_type='image/png')
@app.on_event('startup')
async def startup():
    for d in [UPLOAD_DIR, DATA_DIR, RESULTS_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)
    print(f'\033[1;32m✓ openslam v2.0 started\033[0m')
    print(f'  api: http://{BACKEND_HOST}:{BACKEND_PORT}')
    print(f'  docs: http://{BACKEND_HOST}:{BACKEND_PORT}/docs')
@app.on_event('shutdown')
async def shutdown():
    for client_id, conn in list(ws_connections.items()):
        try:
            await conn['socket'].close()
        except:
            pass
    print(f'\033[1;33m✓ openslam v2.0 shutdown complete\033[0m')
if __name__ == '__main__':
    import uvicorn
    import os
    host = os.getenv('OPENSLAM_BACKEND_HOST', '0.0.0.0')
    port = int(os.getenv('OPENSLAM_BACKEND_PORT', 8007))
    uvicorn.run(app, host=host, port=port)
