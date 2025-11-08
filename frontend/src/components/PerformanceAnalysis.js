import React, { useState, useEffect } from 'react';
const PerformanceAnalysis = ({ executionResults, onNotification, isDarkMode }) => {
  const [activeTab, setActiveTab] = useState('comparison');
  const [selectedResults, setSelectedResults] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [analysisType, setAnalysisType] = useState('comparison');
  const [plotImages, setPlotImages] = useState({});
  const [reportData, setReportData] = useState(null);
  const [benchmarkResults, setBenchmarkResults] = useState([]);
  useEffect(() => {
    if (selectedResults.length >= 2) {
      performComparison();
    }
  }, [selectedResults]);
  const performComparison = async () => {
    if (selectedResults.length < 2) {
      onNotification('Select at least 2 results for comparison', 'error');
      return;
    }
    try {
      const response = await fetch('/api/analysis/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          result_ids: selectedResults.map(r => r.id)
        })
      });
      if (response.ok) {
        const data = await response.json();
        setComparisonData(data);
        loadComparisonPlots(data.comparison_id);
      }
    } catch (error) {
      onNotification('Error performing comparison', 'error');
    }
  };
  const loadComparisonPlots = async (comparisonId) => {
    try {
      const response = await fetch(`/api/analysis/plots/${comparisonId}`);
      if (response.ok) {
        const plots = await response.json();
        setPlotImages(plots);
      }
    } catch (error) {
      onNotification('Error loading comparison plots', 'error');
    }
  };
  const generateReport = async () => {
    if (!comparisonData) {
      onNotification('No comparison data available', 'error');
      return;
    }
    try {
      const response = await fetch('/api/analysis/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          comparison_id: comparisonData.comparison_id,
          format: 'json'
        })
      });
      if (response.ok) {
        const report = await response.json();
        setReportData(report);
        onNotification('Performance report generated', 'success');
      }
    } catch (error) {
      onNotification('Error generating report', 'error');
    }
  };
  const exportReport = async (format) => {
    if (!comparisonData) {
      onNotification('No comparison data to export', 'error');
      return;
    }
    try {
      const response = await fetch('/api/analysis/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          comparison_id: comparisonData.comparison_id,
          format
        })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `performance_analysis.${format}`;
        a.click();
        window.URL.revokeObjectURL(url);
        onNotification(`Report exported as ${format}`, 'success');
      }
    } catch (error) {
      onNotification('Error exporting report', 'error');
    }
  };
  const handleResultSelection = (result, isSelected) => {
    if (isSelected) {
      setSelectedResults(prev => [...prev, result]);
    } else {
      setSelectedResults(prev => prev.filter(r => r.id !== result.id));
    }
  };
  const renderResultSelection = () => (
    <div className="result-selection">
      <h4>Select Results for Analysis</h4>
      <div className="result-list">
        {executionResults.map(result => (
          <div key={result.id} className="result-item">
            <label className="result-checkbox">
              <input 
                type="checkbox"
                checked={selectedResults.some(r => r.id === result.id)}
                onChange={(e) => handleResultSelection(result, e.target.checked)}
              />
              <div className="result-info">
                <div className="result-name">{result.algorithm_name}</div>
                <div className="result-details">
                  <span>Dataset: {result.dataset_name}</span>
                  <span>Time: {new Date(result.timestamp).toLocaleString()}</span>
                </div>
                {result.metrics && (
                  <div className="result-metrics">
                    <span>ATE: {result.metrics.ate?.toFixed(4)}m</span>
                    <span>RPE: {result.metrics.rpe_trans?.toFixed(4)}m</span>
                  </div>
                )}
              </div>
            </label>
          </div>
        ))}
      </div>
      <div className="selection-summary">
        Selected: {selectedResults.length} results
      </div>
    </div>
  );
  const renderComparisonTable = () => {
    if (!comparisonData) return null;
    return (
      <div className="comparison-table">
        <h4>Performance Comparison</h4>
        <table>
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>ATE (m)</th>
              <th>RPE Trans (m)</th>
              <th>RPE Rot (rad)</th>
              <th>Exec Time (s)</th>
              <th>Memory (MB)</th>
              <th>Rank</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(comparisonData.algorithms).map(([algId, data]) => (
              <tr key={algId}>
                <td>{data.name}</td>
                <td>{data.metrics.ate.toFixed(4)}</td>
                <td>{data.metrics.rpe_trans.toFixed(4)}</td>
                <td>{data.metrics.rpe_rot.toFixed(4)}</td>
                <td>{data.metrics.execution_time.toFixed(2)}</td>
                <td>{data.metrics.memory_usage.toFixed(1)}</td>
                <td>
                  {comparisonData.rankings.overall.find(r => r.algorithm_id === algId)?.rank || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };
  const renderRankings = () => {
    if (!comparisonData) return null;
    return (
      <div className="rankings">
        <h4>Performance Rankings</h4>
        <div className="ranking-categories">
          {Object.entries(comparisonData.rankings).map(([metric, rankings]) => (
            <div key={metric} className="ranking-category">
              <h5>{metric.replace('_', ' ').toUpperCase()}</h5>
              <ol>
                {rankings.map(ranking => (
                  <li key={ranking.algorithm_id}>
                    <span className="algorithm-name">
                      {comparisonData.algorithms[ranking.algorithm_id]?.name}
                    </span>
                    <span className="ranking-value">
                      {typeof ranking.value === 'number' ? ranking.value.toFixed(4) : ranking.score}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </div>
      </div>
    );
  };
  const renderSummary = () => {
    if (!comparisonData) return null;
    return (
      <div className="analysis-summary">
        <h4>Analysis Summary</h4>
        <div className="summary-cards">
          <div className="summary-card">
            <div className="card-title">Best Overall</div>
            <div className="card-value">
              {comparisonData.summary.best_ate?.algorithm_id && 
                comparisonData.algorithms[comparisonData.summary.best_ate.algorithm_id]?.name}
            </div>
          </div>
          <div className="summary-card">
            <div className="card-title">Fastest</div>
            <div className="card-value">
              {comparisonData.summary.fastest?.algorithm_id && 
                comparisonData.algorithms[comparisonData.summary.fastest.algorithm_id]?.name}
            </div>
          </div>
          <div className="summary-card">
            <div className="card-title">Most Accurate</div>
            <div className="card-value">
              {comparisonData.summary.best_ate?.algorithm_id && 
                comparisonData.algorithms[comparisonData.summary.best_ate.algorithm_id]?.name}
            </div>
          </div>
          <div className="summary-card">
            <div className="card-title">Memory Efficient</div>
            <div className="card-value">
              {comparisonData.summary.most_memory_efficient?.algorithm_id && 
                comparisonData.algorithms[comparisonData.summary.most_memory_efficient.algorithm_id]?.name}
            </div>
          </div>
        </div>
      </div>
    );
  };
  const renderPlots = () => {
    if (!plotImages || Object.keys(plotImages).length === 0) return null;
    return (
      <div className="analysis-plots">
        <h4>Performance Plots</h4>
        <div className="plots-grid">
          {Object.entries(plotImages).map(([plotType, imageData]) => (
            <div key={plotType} className="plot-container">
              <h5>{plotType.replace('_', ' ').toUpperCase()}</h5>
              <img 
                src={`data:image/png;base64,${imageData}`}
                alt={plotType}
                className="plot-image"
              />
            </div>
          ))}
        </div>
      </div>
    );
  };
  const renderMetricDefinitions = () => (
    <div className="metric-definitions">
      <h4>Metric Definitions</h4>
      <div className="definitions-list">
        <div className="definition-item">
          <div className="definition-term">ATE (Absolute Trajectory Error)</div>
          <div className="definition-desc">
            Root mean square error between estimated and ground truth trajectory after optimal alignment
          </div>
        </div>
        <div className="definition-item">
          <div className="definition-term">RPE Translation</div>
          <div className="definition-desc">
            Root mean square error of relative translation between consecutive poses
          </div>
        </div>
        <div className="definition-item">
          <div className="definition-term">RPE Rotation</div>
          <div className="definition-desc">
            Root mean square error of relative rotation between consecutive poses
          </div>
        </div>
        <div className="definition-item">
          <div className="definition-term">Execution Time</div>
          <div className="definition-desc">
            Total time taken to process the entire dataset
          </div>
        </div>
        <div className="definition-item">
          <div className="definition-term">Memory Usage</div>
          <div className="definition-desc">
            Peak memory consumption during algorithm execution
          </div>
        </div>
      </div>
    </div>
  );
  const renderComparisonTab = () => (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: '0 0 300px' }}>
          {renderResultSelection()}
          <div style={{ marginTop: '20px' }}>
            <button 
              onClick={performComparison}
              disabled={selectedResults.length < 2}
              style={{
                width: '100%',
                padding: '10px',
                background: selectedResults.length >= 2 ? '#4f46e5' : '#94a3b8',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: selectedResults.length >= 2 ? 'pointer' : 'not-allowed',
                marginBottom: '8px'
              }}
            >
              Compare Selected ({selectedResults.length})
            </button>
            <button 
              onClick={generateReport}
              disabled={!comparisonData}
              style={{
                width: '100%',
                padding: '10px',
                background: comparisonData ? '#22c55e' : '#94a3b8',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: comparisonData ? 'pointer' : 'not-allowed'
              }}
            >
              Generate Report
            </button>
          </div>
        </div>
        <div style={{ flex: 1 }}>
          {comparisonData ? (
            <div>
              {renderSummary()}
              {renderComparisonTable()}
              {renderRankings()}
              {renderPlots()}
            </div>
          ) : (
            <div style={{
              background: isDarkMode ? '#1a1a1a' : 'white',
              border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
              borderRadius: '8px',
              padding: '40px 20px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '16px', opacity: 0.3 }}>📊</div>
              <h4 style={{ margin: '0 0 8px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                No Comparison Results
              </h4>
              <p style={{ margin: 0, color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                Select at least 2 execution results to perform comparison analysis
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderBenchmarkTab = () => (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 16px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
          Algorithm Benchmarks
        </h3>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <select style={{
            padding: '8px 12px',
            border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
            borderRadius: '6px',
            background: isDarkMode ? '#334155' : 'white',
            color: isDarkMode ? '#e2e8f0' : '#1e293b'
          }}>
            <option>KITTI Dataset</option>
            <option>EuRoC Dataset</option>
            <option>TUM RGB-D Dataset</option>
          </select>
          <button style={{
            padding: '8px 16px',
            background: '#4f46e5',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}>
            Run Benchmark
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '8px',
          padding: '16px'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
            Accuracy Benchmark
          </h4>
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: isDarkMode ? '#94a3b8' : '#64748b' }}>Accuracy chart placeholder</span>
          </div>
        </div>

        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '8px',
          padding: '16px'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
            Speed Benchmark
          </h4>
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: isDarkMode ? '#94a3b8' : '#64748b' }}>Speed chart placeholder</span>
          </div>
        </div>

        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '8px',
          padding: '16px'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
            Memory Usage
          </h4>
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: isDarkMode ? '#94a3b8' : '#64748b' }}>Memory chart placeholder</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderMetricsTab = () => (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 16px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
          Performance Metrics
        </h3>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div>
          {renderMetricDefinitions()}
        </div>
        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h4 style={{ margin: '0 0 16px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
            Metric Calculator
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <select style={{
              padding: '8px 12px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '6px',
              background: isDarkMode ? '#334155' : 'white',
              color: isDarkMode ? '#e2e8f0' : '#1e293b'
            }}>
              <option>Select Result</option>
              {executionResults.map(result => (
                <option key={result.id} value={result.id}>
                  {result.algorithm_name} - {new Date(result.timestamp).toLocaleDateString()}
                </option>
              ))}
            </select>
            <button style={{
              padding: '8px 16px',
              background: '#4f46e5',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}>
              Calculate Metrics
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: isDarkMode ? '#0f0f0f' : '#f8fafc',
      color: isDarkMode ? '#e0e0e0' : '#1e293b'
    }}>
      <div style={{
        padding: '16px 20px',
        background: isDarkMode ? '#1a1a1a' : 'white',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
      }}>
        <h1 style={{ margin: '0 0 4px 0', fontSize: '1.5rem', fontWeight: '600' }}>
          Performance Analysis
        </h1>
        <p style={{ margin: 0, color: isDarkMode ? '#94a3b8' : '#64748b', fontSize: '0.9rem' }}>
          Compare algorithms, run benchmarks, and analyze performance metrics
        </p>
      </div>

      <div style={{
        display: 'flex',
        background: isDarkMode ? '#1a1a1a' : 'white',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
      }}>
        {[
          { id: 'comparison', label: 'Algorithm Comparison', icon: '⚖️' },
          { id: 'benchmark', label: 'Benchmarks', icon: '🏁' },
          { id: 'metrics', label: 'Metrics & Definitions', icon: '📏' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '12px 20px',
              border: 'none',
              background: activeTab === tab.id 
                ? (isDarkMode ? '#334155' : '#f1f5f9') 
                : 'transparent',
              color: activeTab === tab.id 
                ? (isDarkMode ? '#e2e8f0' : '#4f46e5') 
                : (isDarkMode ? '#94a3b8' : '#64748b'),
              borderBottom: activeTab === tab.id ? '2px solid #4f46e5' : '2px solid transparent',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s ease'
            }}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {activeTab === 'comparison' && renderComparisonTab()}
        {activeTab === 'benchmark' && renderBenchmarkTab()}
        {activeTab === 'metrics' && renderMetricsTab()}
      </div>
    </div>
  );
};
export default PerformanceAnalysis;