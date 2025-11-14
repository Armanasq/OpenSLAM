# OpenSLAM API Documentation

Complete REST API with WebSocket support for the OpenSLAM SLAM Evaluation Framework.

## Quick Start

### 1. Start the Server

```bash
./run_server.sh
```

The server will start on `http://localhost:5000`

### 2. Open the Frontend

Open `frontend/index.html` in your web browser, or serve it using:

```bash
cd frontend
python3 -m http.server 8080
```

Then visit `http://localhost:8080`

## API Endpoints

### Plugins

#### List all plugins
```
GET /api/plugins
```

Response:
```json
{
  "success": true,
  "plugins": [
    {
      "name": "ORB-SLAM3",
      "version": "1.0.0",
      "type": "visual",
      "description": "Feature-based visual SLAM",
      "author": "UZ Research",
      "input_types": ["image", "stereo"],
      "output_format": "trajectory",
      "status": "active",
      "language": "python"
    }
  ],
  "count": 1
}
```

#### Get plugin details
```
GET /api/plugins/<plugin_name>
```

### Datasets

#### List all datasets
```
GET /api/datasets
```

Response:
```json
{
  "success": true,
  "datasets": [
    {
      "id": "kitti-00",
      "name": "KITTI-00",
      "format": "KITTI",
      "sequences": 11,
      "frames": 4540,
      "size": 2684354560,
      "uploaded": "2025-01-10T10:30:00",
      "status": "ready",
      "path": "/data/datasets/kitti-00"
    }
  ],
  "count": 1
}
```

#### Upload dataset
```
POST /api/datasets
Content-Type: multipart/form-data

file: <dataset_file>
name: <dataset_name>
format: <dataset_format>
```

#### Delete dataset
```
DELETE /api/datasets/<dataset_id>
```

### Evaluations

#### Create evaluation
```
POST /api/evaluations
Content-Type: application/json

{
  "plugin": "ORB-SLAM3",
  "dataset": "kitti-00",
  "parameters": {
    "features": 1000,
    "scaleFactor": 1.2,
    "levels": 8
  }
}
```

Response:
```json
{
  "success": true,
  "id": "eval_1705749000123",
  "message": "Evaluation started"
}
```

#### List evaluations
```
GET /api/evaluations
```

#### Get evaluation results
```
GET /api/evaluations/<eval_id>
```

Response:
```json
{
  "success": true,
  "result": {
    "id": "eval_1705749000123",
    "plugin": "ORB-SLAM3",
    "dataset": "KITTI-00",
    "status": "completed",
    "ate": 0.145,
    "rpe": 0.023,
    "execution_time": 3600,
    "success_rate": 98.5,
    "trajectory": [[...], [...], ...],
    "started_at": "2025-01-10T11:00:00",
    "completed_at": "2025-01-10T12:00:00"
  }
}
```

### Comparison

#### Compare results
```
POST /api/compare
Content-Type: application/json

{
  "ids": ["eval_1", "eval_2", "eval_3"]
}
```

### Batch Evaluations

#### Create batch
```
POST /api/batch
Content-Type: application/json

{
  "name": "KITTI Benchmark",
  "plugins": ["ORB-SLAM3", "VINS-Mono", "DSO"],
  "datasets": ["kitti-00", "kitti-05", "kitti-07"]
}
```

Response:
```json
{
  "success": true,
  "batch_id": "batch_1705749000456",
  "message": "Batch created successfully"
}
```

#### List batches
```
GET /api/batch
```

#### Get batch details
```
GET /api/batch/<batch_id>
```

#### Cancel batch
```
POST /api/batch/<batch_id>/cancel
```

### System

#### Get system status
```
GET /api/system/status
```

Response:
```json
{
  "success": true,
  "status": {
    "online": true,
    "version": "1.0.0",
    "plugins_count": 6,
    "running_evaluations": 2,
    "timestamp": "2025-01-10T12:30:00"
  }
}
```

#### Get settings
```
GET /api/system/settings
```

#### Update settings
```
PUT /api/system/settings
Content-Type: application/json

{
  "theme": "dark",
  "maxConcurrentEvaluations": 5,
  "autoSave": true
}
```

## WebSocket Events

The server uses Socket.IO for real-time updates.

### Connect
```javascript
const socket = io('http://localhost:5000');
```

### Events

#### evaluation_progress
Emitted during evaluation execution:
```json
{
  "id": "eval_1705749000123",
  "progress": 45,
  "stage": "Running SLAM algorithm",
  "message": "Processing frame 450/1000",
  "timestamp": "2025-01-10T11:30:00"
}
```

#### evaluation_error
Emitted when evaluation fails:
```json
{
  "id": "eval_1705749000123",
  "error": "Dataset not found"
}
```

#### connected
Emitted when client connects:
```json
{
  "message": "Connected to OpenSLAM server"
}
```

### Subscribe to evaluation updates
```javascript
socket.emit('subscribe_evaluation', { id: 'eval_1705749000123' });

socket.on('evaluation_progress', (data) => {
  console.log(`Progress: ${data.progress}%`);
  console.log(`Stage: ${data.stage}`);
});
```

## Error Handling

All API endpoints return standardized error responses:

```json
{
  "success": false,
  "error": "Error message here"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

## Core Integration

The API server integrates with OpenSLAM core modules:

- **PluginManager**: Discovery and validation of SLAM plugins
- **PluginExecutor**: Execution of SLAM algorithms
- **ConnectorEngine**: Data transformation and parsing
- **WorkflowExecutor**: Multi-stage workflow orchestration
- **EvaluationMetrics**: Trajectory error calculation (ATE, RPE)
- **DockerOrchestrator**: Container-based plugin execution

## File Structure

```
api/
  server.py          - Main Flask application
  requirements.txt   - Python dependencies

data/
  uploads/          - Temporary file uploads
  datasets/         - Dataset storage
  results/          - Evaluation results (JSON)

frontend/
  index.html        - Main application
  scripts/
    api.js          - API client with Socket.IO
    app.js          - Application initialization
    config.js       - Configuration
    components.js   - UI components
    utils.js        - Utility functions
    views/          - View implementations
  styles/           - CSS files
```

## Development

### Adding New Endpoints

1. Add route handler in `api/server.py`:
```python
@app.route('/api/your-endpoint', methods=['GET'])
def your_endpoint():
    try:
        # Your logic here
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

2. Add frontend API method in `frontend/scripts/api.js`:
```javascript
yourModule: {
    yourMethod() {
        return API.get('/your-endpoint');
    }
}
```

### Running in Production

For production deployment, use a production WSGI server:

```bash
pip install gunicorn gevent-websocket

gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
         --workers 4 \
         --bind 0.0.0.0:5000 \
         api.server:app
```

## Testing

Test API endpoints using curl:

```bash
# List plugins
curl http://localhost:5000/api/plugins

# Create evaluation
curl -X POST http://localhost:5000/api/evaluations \
  -H "Content-Type: application/json" \
  -d '{"plugin":"ORB-SLAM3","dataset":"kitti-00"}'

# Get evaluation status
curl http://localhost:5000/api/evaluations/eval_1705749000123
```

## License

Same as OpenSLAM framework license.
