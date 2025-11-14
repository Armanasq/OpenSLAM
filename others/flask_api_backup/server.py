#!/usr/bin/env python3
"""
OpenSLAM API Server
Complete REST API with WebSocket support for the OpenSLAM framework
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import sys
import json
import threading
import time
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.plugin_manager import PluginManager
from core.plugin_executor import PluginExecutor
from core.connector_engine import ConnectorEngine
from core.workflow_executor import WorkflowExecutor
from core.evaluation_metrics import EvaluationMetrics
from core.docker_orchestrator import DockerOrchestrator

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'openslam-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
app.config['RESULTS_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')
app.config['DATASETS_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'data', 'datasets')

# Enable CORS for frontend
CORS(app)

# Initialize SocketIO for WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATASETS_FOLDER'], exist_ok=True)

# Initialize core components
plugin_manager = PluginManager()
connector_engine = ConnectorEngine()
metrics_calculator = EvaluationMetrics()

# Global state for running evaluations
running_evaluations = {}
evaluation_results = {}


# ============================================================================
# Helper Functions
# ============================================================================

def get_evaluation_id():
    """Generate unique evaluation ID"""
    return f"eval_{int(time.time() * 1000)}"


def emit_progress(eval_id, progress, stage, message):
    """Emit progress update via WebSocket"""
    socketio.emit('evaluation_progress', {
        'id': eval_id,
        'progress': progress,
        'stage': stage,
        'message': message,
        'timestamp': datetime.now().isoformat()
    })


def run_evaluation_background(eval_id, plugin_name, dataset_path, parameters):
    """Run evaluation in background thread"""
    try:
        running_evaluations[eval_id] = {
            'status': 'running',
            'progress': 0,
            'plugin': plugin_name,
            'dataset': dataset_path,
            'started_at': datetime.now().isoformat()
        }

        emit_progress(eval_id, 10, 'Initializing plugin', f'Loading {plugin_name}...')

        # Initialize executor
        executor = PluginExecutor(plugin_name)

        emit_progress(eval_id, 20, 'Loading dataset', f'Reading dataset from {dataset_path}...')

        # Detect dataset format
        dataset_format = detect_dataset_format(dataset_path)

        emit_progress(eval_id, 30, 'Running SLAM algorithm', 'Processing frames...')

        # Run evaluation
        result, error = executor.run_on_dataset(dataset_path, dataset_format)

        if error:
            raise Exception(error)

        emit_progress(eval_id, 70, 'Computing metrics', 'Calculating trajectory error...')

        # Calculate metrics
        ground_truth_path = os.path.join(dataset_path, 'groundtruth.txt')
        if os.path.exists(ground_truth_path):
            estimated_trajectory = result['trajectory']
            ate, rpe = metrics_calculator.calculate_all_metrics(
                estimated_trajectory,
                ground_truth_path
            )
        else:
            ate, rpe = None, None

        emit_progress(eval_id, 90, 'Saving results', 'Writing output files...')

        # Save results
        result_data = {
            'id': eval_id,
            'plugin': plugin_name,
            'dataset': os.path.basename(dataset_path),
            'dataset_path': dataset_path,
            'parameters': parameters,
            'trajectory': result['trajectory'].tolist() if result['trajectory'] is not None else None,
            'ate': ate,
            'rpe': rpe,
            'execution_time': result.get('execution_time', 0),
            'success_rate': 100.0 if error is None else 0.0,
            'status': 'completed',
            'started_at': running_evaluations[eval_id]['started_at'],
            'completed_at': datetime.now().isoformat()
        }

        # Save to file
        result_file = os.path.join(app.config['RESULTS_FOLDER'], f'{eval_id}.json')
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        evaluation_results[eval_id] = result_data
        running_evaluations[eval_id]['status'] = 'completed'
        running_evaluations[eval_id]['progress'] = 100

        emit_progress(eval_id, 100, 'Completed', 'Evaluation completed successfully')

    except Exception as e:
        error_msg = str(e)
        running_evaluations[eval_id]['status'] = 'failed'
        running_evaluations[eval_id]['error'] = error_msg

        evaluation_results[eval_id] = {
            'id': eval_id,
            'plugin': plugin_name,
            'dataset': dataset_path,
            'status': 'failed',
            'error': error_msg,
            'started_at': running_evaluations[eval_id]['started_at'],
            'completed_at': datetime.now().isoformat()
        }

        socketio.emit('evaluation_error', {
            'id': eval_id,
            'error': error_msg
        })


def detect_dataset_format(dataset_path):
    """Detect dataset format from path"""
    path_lower = dataset_path.lower()
    if 'kitti' in path_lower:
        return 'kitti'
    elif 'euroc' in path_lower:
        return 'euroc'
    elif 'tum' in path_lower:
        return 'tum'
    return 'auto'


# ============================================================================
# Plugin Management API
# ============================================================================

@app.route('/api/plugins', methods=['GET'])
def list_plugins():
    """List all available plugins"""
    try:
        plugins = plugin_manager.list_plugins()

        plugin_list = []
        for name, config in plugins.items():
            plugin_info = {
                'name': name,
                'version': config.get('version', '1.0.0'),
                'type': config.get('type', 'unknown'),
                'description': config.get('description', ''),
                'author': config.get('author', 'Unknown'),
                'input_types': config.get('input_types', []),
                'output_format': config.get('output_format', 'trajectory'),
                'status': 'active',
                'language': config.get('language', 'python')
            }
            plugin_list.append(plugin_info)

        return jsonify({
            'success': True,
            'plugins': plugin_list,
            'count': len(plugin_list)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/plugins/<plugin_name>', methods=['GET'])
def get_plugin(plugin_name):
    """Get detailed information about a specific plugin"""
    try:
        plugins = plugin_manager.list_plugins()

        if plugin_name not in plugins:
            return jsonify({
                'success': False,
                'error': f'Plugin {plugin_name} not found'
            }), 404

        config = plugins[plugin_name]

        plugin_info = {
            'name': plugin_name,
            'version': config.get('version', '1.0.0'),
            'type': config.get('type', 'unknown'),
            'description': config.get('description', ''),
            'author': config.get('author', 'Unknown'),
            'input_types': config.get('input_types', []),
            'output_format': config.get('output_format', 'trajectory'),
            'parameters': config.get('parameters', {}),
            'docker': config.get('docker', {}),
            'workflow': config.get('workflow', {}),
            'language': config.get('language', 'python')
        }

        return jsonify({
            'success': True,
            'plugin': plugin_info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# Dataset Management API
# ============================================================================

@app.route('/api/datasets', methods=['GET'])
def list_datasets():
    """List all available datasets"""
    try:
        datasets = []
        datasets_path = Path(app.config['DATASETS_FOLDER'])

        for dataset_dir in datasets_path.iterdir():
            if dataset_dir.is_dir():
                # Get dataset info
                info_file = dataset_dir / 'info.json'
                if info_file.exists():
                    with open(info_file, 'r') as f:
                        info = json.load(f)
                else:
                    # Create basic info
                    info = {
                        'name': dataset_dir.name,
                        'format': detect_dataset_format(str(dataset_dir)),
                        'sequences': 1,
                        'uploaded': datetime.fromtimestamp(dataset_dir.stat().st_mtime).isoformat()
                    }

                # Calculate size
                total_size = sum(f.stat().st_size for f in dataset_dir.rglob('*') if f.is_file())

                # Count frames
                frames = len(list(dataset_dir.glob('*.png'))) + len(list(dataset_dir.glob('*.jpg')))

                dataset_info = {
                    'id': dataset_dir.name,
                    'name': info.get('name', dataset_dir.name),
                    'format': info.get('format', 'custom'),
                    'sequences': info.get('sequences', 1),
                    'frames': frames,
                    'size': total_size,
                    'uploaded': info.get('uploaded'),
                    'status': 'ready',
                    'path': str(dataset_dir)
                }

                datasets.append(dataset_info)

        return jsonify({
            'success': True,
            'datasets': datasets,
            'count': len(datasets)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/datasets/<dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """Get detailed information about a specific dataset"""
    try:
        dataset_path = Path(app.config['DATASETS_FOLDER']) / dataset_id

        if not dataset_path.exists():
            return jsonify({
                'success': False,
                'error': f'Dataset {dataset_id} not found'
            }), 404

        # Get dataset info
        info_file = dataset_path / 'info.json'
        if info_file.exists():
            with open(info_file, 'r') as f:
                info = json.load(f)
        else:
            info = {
                'name': dataset_id,
                'format': detect_dataset_format(str(dataset_path))
            }

        return jsonify({
            'success': True,
            'dataset': info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/datasets', methods=['POST'])
def upload_dataset():
    """Upload a new dataset"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty filename'
            }), 400

        # Save file
        filename = secure_filename(file.filename)
        dataset_id = f"dataset_{int(time.time())}"
        dataset_path = Path(app.config['DATASETS_FOLDER']) / dataset_id
        dataset_path.mkdir(exist_ok=True)

        file_path = dataset_path / filename
        file.save(file_path)

        # Create info file
        info = {
            'name': request.form.get('name', filename),
            'format': request.form.get('format', 'custom'),
            'uploaded': datetime.now().isoformat()
        }

        with open(dataset_path / 'info.json', 'w') as f:
            json.dump(info, f, indent=2)

        return jsonify({
            'success': True,
            'dataset_id': dataset_id,
            'message': 'Dataset uploaded successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/datasets/<dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    """Delete a dataset"""
    try:
        dataset_path = Path(app.config['DATASETS_FOLDER']) / dataset_id

        if not dataset_path.exists():
            return jsonify({
                'success': False,
                'error': f'Dataset {dataset_id} not found'
            }), 404

        # Delete directory
        import shutil
        shutil.rmtree(dataset_path)

        return jsonify({
            'success': True,
            'message': 'Dataset deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# Evaluation API
# ============================================================================

@app.route('/api/evaluations', methods=['POST'])
def create_evaluation():
    """Create and start a new evaluation"""
    try:
        data = request.json

        plugin_name = data.get('plugin')
        dataset_id = data.get('dataset')
        parameters = data.get('parameters', {})

        if not plugin_name or not dataset_id:
            return jsonify({
                'success': False,
                'error': 'Plugin and dataset are required'
            }), 400

        # Get dataset path
        dataset_path = Path(app.config['DATASETS_FOLDER']) / dataset_id
        if not dataset_path.exists():
            return jsonify({
                'success': False,
                'error': f'Dataset {dataset_id} not found'
            }), 404

        # Generate evaluation ID
        eval_id = get_evaluation_id()

        # Start evaluation in background thread
        thread = threading.Thread(
            target=run_evaluation_background,
            args=(eval_id, plugin_name, str(dataset_path), parameters)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'id': eval_id,
            'message': 'Evaluation started'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/evaluations', methods=['GET'])
def list_evaluations():
    """List all evaluations"""
    try:
        evaluations = []

        # Load from results folder
        results_path = Path(app.config['RESULTS_FOLDER'])
        for result_file in results_path.glob('*.json'):
            with open(result_file, 'r') as f:
                result = json.load(f)
                evaluations.append(result)

        # Add running evaluations
        for eval_id, info in running_evaluations.items():
            if info['status'] == 'running' and eval_id not in evaluation_results:
                evaluations.append({
                    'id': eval_id,
                    'plugin': info['plugin'],
                    'dataset': os.path.basename(info['dataset']),
                    'status': 'running',
                    'progress': info['progress'],
                    'started_at': info['started_at']
                })

        return jsonify({
            'success': True,
            'results': evaluations,
            'count': len(evaluations)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/evaluations/<eval_id>', methods=['GET'])
def get_evaluation(eval_id):
    """Get detailed evaluation results"""
    try:
        # Check if in memory
        if eval_id in evaluation_results:
            return jsonify({
                'success': True,
                'result': evaluation_results[eval_id]
            })

        # Check if in file
        result_file = Path(app.config['RESULTS_FOLDER']) / f'{eval_id}.json'
        if result_file.exists():
            with open(result_file, 'r') as f:
                result = json.load(f)
            return jsonify({
                'success': True,
                'result': result
            })

        # Check if running
        if eval_id in running_evaluations:
            return jsonify({
                'success': True,
                'result': {
                    'id': eval_id,
                    'status': running_evaluations[eval_id]['status'],
                    'progress': running_evaluations[eval_id].get('progress', 0)
                }
            })

        return jsonify({
            'success': False,
            'error': f'Evaluation {eval_id} not found'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# Comparison API
# ============================================================================

@app.route('/api/compare', methods=['POST'])
def compare_results():
    """Compare multiple evaluation results"""
    try:
        data = request.json
        eval_ids = data.get('ids', [])

        if len(eval_ids) < 2:
            return jsonify({
                'success': False,
                'error': 'At least 2 evaluations required for comparison'
            }), 400

        results = []
        for eval_id in eval_ids:
            result_file = Path(app.config['RESULTS_FOLDER']) / f'{eval_id}.json'
            if result_file.exists():
                with open(result_file, 'r') as f:
                    results.append(json.load(f))

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# Batch Evaluation API
# ============================================================================

batch_jobs = {}


@app.route('/api/batch', methods=['POST'])
def create_batch():
    """Create a new batch evaluation"""
    try:
        data = request.json

        plugins = data.get('plugins', [])
        datasets = data.get('datasets', [])

        if not plugins or not datasets:
            return jsonify({
                'success': False,
                'error': 'Plugins and datasets are required'
            }), 400

        batch_id = f"batch_{int(time.time() * 1000)}"

        batch_jobs[batch_id] = {
            'id': batch_id,
            'name': data.get('name', f'Batch {batch_id}'),
            'plugins': len(plugins),
            'datasets': len(datasets),
            'total': len(plugins) * len(datasets),
            'completed': 0,
            'failed': 0,
            'running': 0,
            'pending': len(plugins) * len(datasets),
            'created': datetime.now().isoformat(),
            'status': 'pending',
            'evaluations': []
        }

        # Create evaluation matrix
        for plugin in plugins:
            for dataset in datasets:
                eval_id = get_evaluation_id()
                batch_jobs[batch_id]['evaluations'].append({
                    'id': eval_id,
                    'plugin': plugin,
                    'dataset': dataset,
                    'status': 'pending'
                })

        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'message': 'Batch created successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/batch', methods=['GET'])
def list_batches():
    """List all batch jobs"""
    try:
        batches = list(batch_jobs.values())

        return jsonify({
            'success': True,
            'batches': batches,
            'count': len(batches)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/batch/<batch_id>', methods=['GET'])
def get_batch(batch_id):
    """Get batch job details"""
    try:
        if batch_id not in batch_jobs:
            return jsonify({
                'success': False,
                'error': f'Batch {batch_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'batch': batch_jobs[batch_id]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/batch/<batch_id>/cancel', methods=['POST'])
def cancel_batch(batch_id):
    """Cancel a batch job"""
    try:
        if batch_id not in batch_jobs:
            return jsonify({
                'success': False,
                'error': f'Batch {batch_id} not found'
            }), 404

        batch_jobs[batch_id]['status'] = 'cancelled'

        return jsonify({
            'success': True,
            'message': 'Batch cancelled successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# System API
# ============================================================================

system_settings = {
    'theme': 'light',
    'language': 'en',
    'autoSave': True,
    'notifications': True,
    'defaultMetric': 'ate',
    'maxConcurrentEvaluations': 3,
    'cacheResults': True,
    'logLevel': 'info',
    'dataPath': '/data/openslam',
    'maxStorageSize': 100,
    'autoCleanup': True,
    'retentionDays': 30
}


@app.route('/api/system/status', methods=['GET'])
def system_status():
    """Get system status"""
    try:
        return jsonify({
            'success': True,
            'status': {
                'online': True,
                'version': '1.0.0',
                'plugins_count': len(plugin_manager.list_plugins()),
                'running_evaluations': len([e for e in running_evaluations.values() if e['status'] == 'running']),
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/system/settings', methods=['GET'])
def get_settings():
    """Get system settings"""
    try:
        return jsonify({
            'success': True,
            'settings': system_settings
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/system/settings', methods=['PUT'])
def update_settings():
    """Update system settings"""
    try:
        data = request.json
        system_settings.update(data)

        return jsonify({
            'success': True,
            'settings': system_settings,
            'message': 'Settings updated successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# WebSocket Events
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to OpenSLAM server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')


@socketio.on('subscribe_evaluation')
def handle_subscribe_evaluation(data):
    """Subscribe to evaluation updates"""
    eval_id = data.get('id')
    print(f'Client subscribed to evaluation: {eval_id}')


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print('Starting OpenSLAM API Server...')
    print(f'Upload folder: {app.config["UPLOAD_FOLDER"]}')
    print(f'Results folder: {app.config["RESULTS_FOLDER"]}')
    print(f'Datasets folder: {app.config["DATASETS_FOLDER"]}')
    print('Server running on http://localhost:5000')

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
