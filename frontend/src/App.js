import React, { useState, useEffect } from 'react';
import './App.css';
const API = 'http://localhost:8007';
function App() {
  const [view, setView] = useState('datasets');
  const [datasets, setDatasets] = useState([]);
  const [algorithms, setAlgorithms] = useState([]);
  const [runs, setRuns] = useState([]);
  const [ws, setWs] = useState(null);
  useEffect(() => {
    loadData();
    connectWS();
  }, []);
  const connectWS = () => {
    const socket = new WebSocket(`ws://localhost:8007/ws/client_${Date.now()}`);
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'complete') loadData();
    };
    setWs(socket);
  };
  const loadData = async () => {
    const [ds, alg, rn] = await Promise.all([fetch(`${API}/api/datasets`).then(r => r.json()), fetch(`${API}/api/algorithms`).then(r => r.json()), fetch(`${API}/api/runs`).then(r => r.json())]);
    setDatasets(ds.datasets || []);
    setAlgorithms(alg.algorithms || []);
    setRuns(rn.runs || []);
  };
  return (
    <div className="app">
      <header className="header">
        <h1>OpenSLAM</h1>
        <nav>
          <button onClick={() => setView('datasets')} className={view === 'datasets' ? 'active' : ''}>datasets</button>
          <button onClick={() => setView('algorithms')} className={view === 'algorithms' ? 'active' : ''}>algorithms</button>
          <button onClick={() => setView('runs')} className={view === 'runs' ? 'active' : ''}>runs</button>
          <button onClick={() => setView('results')} className={view === 'results' ? 'active' : ''}>results</button>
        </nav>
      </header>
      <main className="main">
        {view === 'datasets' && <Datasets datasets={datasets} onUpdate={loadData} />}
        {view === 'algorithms' && <Algorithms algorithms={algorithms} onUpdate={loadData} />}
        {view === 'runs' && <Runs datasets={datasets} algorithms={algorithms} runs={runs} onUpdate={loadData} />}
        {view === 'results' && <Results runs={runs} />}
      </main>
    </div>
  );
}
function Datasets({ datasets, onUpdate }) {
  const [uploading, setUploading] = useState(false);
  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append('file', file);
    await fetch(`${API}/api/upload`, { method: 'POST', body: form });
    setUploading(false);
    onUpdate();
  };
  const handleProcess = async (id) => {
    await fetch(`${API}/api/dataset/${id}/process`, { method: 'POST' });
    onUpdate();
  };
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>datasets</h2>
        <label className="button primary">
          {uploading ? 'uploading...' : 'upload dataset'}
          <input type="file" onChange={handleUpload} style={{ display: 'none' }} />
        </label>
      </div>
      <div className="list">
        {datasets.map(ds => (
          <div key={ds.id} className="item">
            <div className="item-header">
              <h3>{ds.name}</h3>
              <span className={`badge ${ds.status}`}>{ds.status}</span>
            </div>
            <div className="item-body">
              <p>format: {ds.format}</p>
              <p>valid: {ds.valid ? 'yes' : 'no'}</p>
              {ds.errors && ds.errors.length > 0 && <p className="error">errors: {ds.errors.join(', ')}</p>}
            </div>
            {ds.status === 'uploaded' && <button onClick={() => handleProcess(ds.id)} className="button">process</button>}
          </div>
        ))}
        {datasets.length === 0 && <div className="empty">no datasets uploaded</div>}
      </div>
    </div>
  );
}
function Algorithms({ algorithms, onUpdate }) {
  const [show, setShow] = useState(false);
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const handleCreate = async () => {
    await fetch(`${API}/api/algorithm`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, code }) });
    setShow(false);
    setName('');
    setCode('');
    onUpdate();
  };
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>algorithms</h2>
        <button onClick={() => setShow(true)} className="button primary">create algorithm</button>
      </div>
      <div className="list">
        {algorithms.map(alg => (
          <div key={alg.id} className="item">
            <h3>{alg.name}</h3>
            <p>id: {alg.id}</p>
          </div>
        ))}
        {algorithms.length === 0 && <div className="empty">no algorithms created</div>}
      </div>
      {show && (
        <div className="modal">
          <div className="modal-content">
            <h2>create algorithm</h2>
            <input type="text" placeholder="name" value={name} onChange={(e) => setName(e.target.value)} className="input" />
            <textarea placeholder="code" value={code} onChange={(e) => setCode(e.target.value)} className="textarea" rows={20} />
            <div className="modal-actions">
              <button onClick={handleCreate} className="button primary">create</button>
              <button onClick={() => setShow(false)} className="button">cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
function Runs({ datasets, algorithms, runs, onUpdate }) {
  const [datasetId, setDatasetId] = useState('');
  const [algorithmId, setAlgorithmId] = useState('');
  const [running, setRunning] = useState(false);
  const processedDatasets = datasets.filter(d => d.status === 'processed');
  const handleRun = async () => {
    if (!datasetId || !algorithmId) return;
    setRunning(true);
    await fetch(`${API}/api/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ dataset_id: datasetId, algorithm_id: algorithmId }) });
    setRunning(false);
    onUpdate();
  };
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>runs</h2>
      </div>
      <div className="form">
        <select value={datasetId} onChange={(e) => setDatasetId(e.target.value)} className="select">
          <option value="">select dataset</option>
          {processedDatasets.map(ds => <option key={ds.id} value={ds.id}>{ds.name}</option>)}
        </select>
        <select value={algorithmId} onChange={(e) => setAlgorithmId(e.target.value)} className="select">
          <option value="">select algorithm</option>
          {algorithms.map(alg => <option key={alg.id} value={alg.id}>{alg.name}</option>)}
        </select>
        <button onClick={handleRun} disabled={!datasetId || !algorithmId || running} className="button primary">{running ? 'running...' : 'start run'}</button>
      </div>
      <div className="list">
        {runs.map(run => (
          <div key={run.id} className="item">
            <div className="item-header">
              <h3>run {run.id}</h3>
              <span className={`badge ${run.status}`}>{run.status}</span>
            </div>
            <div className="item-body">
              <p>dataset: {run.dataset_id}</p>
              <p>algorithm: {run.algorithm_id}</p>
              {run.metrics && (
                <div className="metrics">
                  <p>ate rmse: {run.metrics.ate?.rmse?.toFixed(3)}m</p>
                  <p>rpe trans: {run.metrics.rpe?.trans_rmse?.toFixed(3)}m</p>
                  <p>robustness: {run.metrics.robustness?.toFixed(1)}/100</p>
                </div>
              )}
            </div>
          </div>
        ))}
        {runs.length === 0 && <div className="empty">no runs executed</div>}
      </div>
    </div>
  );
}
function Results({ runs }) {
  const [selected, setSelected] = useState(null);
  const completed = runs.filter(r => r.status === 'completed');
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>results</h2>
      </div>
      <div className="results">
        <div className="results-sidebar">
          {completed.map(run => (
            <div key={run.id} onClick={() => setSelected(run)} className={`result-item ${selected?.id === run.id ? 'active' : ''}`}>
              <h4>run {run.id}</h4>
              <p>{run.algorithm_id}</p>
            </div>
          ))}
          {completed.length === 0 && <div className="empty">no completed runs</div>}
        </div>
        <div className="results-content">
          {selected ? (
            <>
              <h2>run {selected.id}</h2>
              {selected.metrics && (
                <div className="metrics-grid">
                  <div className="metric-card">
                    <h4>ate rmse</h4>
                    <p className="metric-value">{selected.metrics.ate?.rmse?.toFixed(3)}m</p>
                  </div>
                  <div className="metric-card">
                    <h4>rpe trans</h4>
                    <p className="metric-value">{selected.metrics.rpe?.trans_rmse?.toFixed(3)}m</p>
                  </div>
                  <div className="metric-card">
                    <h4>robustness</h4>
                    <p className="metric-value">{selected.metrics.robustness?.toFixed(1)}/100</p>
                  </div>
                  <div className="metric-card">
                    <h4>alignment quality</h4>
                    <p className="metric-value">{selected.alignment?.quality?.rmse?.toFixed(3)}m</p>
                  </div>
                </div>
              )}
              {selected.plots && (
                <div className="plots">
                  <h3>plots</h3>
                  {Object.entries(selected.plots).map(([key, path]) => (
                    <div key={key} className="plot">
                      <h4>{key.replace(/_/g, ' ')}</h4>
                      <img src={`${API}/api/plot/${path}`} alt={key} />
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="empty">select a run to view results</div>
          )}
        </div>
      </div>
    </div>
  );
}
export default App;
