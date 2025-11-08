import React, { useState, useEffect } from 'react';
import TrajectoryVisualization from './TrajectoryVisualization';
import PointCloudVisualization from './PointCloudVisualization';

const Visualization = ({ executionResults, currentDataset, onNotification, isDarkMode }) => {
  const [activeTab, setActiveTab] = useState('results');
  const [selectedResult, setSelectedResult] = useState(null);
  const [visualizationType, setVisualizationType] = useState('trajectory');
  const [trajectoryData, setTrajectoryData] = useState(null);
  const [groundTruthData, setGroundTruthData] = useState(null);
  const [pointCloudData, setPointCloudData] = useState(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [comparisonResults, setComparisonResults] = useState([]);
  useEffect(() => {
    if (executionResults.length > 0) {
      setSelectedResult(executionResults[executionResults.length - 1]);
    }
  }, [executionResults]);
  useEffect(() => {
    if (selectedResult) {
      loadVisualizationData();
    }
  }, [selectedResult, visualizationType]);
  useEffect(() => {
    if (currentDataset) {
      loadGroundTruthData();
    }
  }, [currentDataset]);
  const loadVisualizationData = async () => {
    if (!selectedResult) return;
    try {
      const response = await fetch(`/api/results/${selectedResult.id}/visualization`);
      if (response.ok) {
        const data = await response.json();
        setTrajectoryData(data.trajectory);
        setPointCloudData(data.point_cloud);
      }
    } catch (error) {
      onNotification('Error loading visualization data', 'error');
    }
  };
  const loadGroundTruthData = async () => {
    if (!currentDataset) return;
    try {
      const response = await fetch(`/api/datasets/${currentDataset.id}/ground-truth`);
      if (response.ok) {
        const data = await response.json();
        setGroundTruthData(data.trajectory);
      }
    } catch (error) {
      console.log('No ground truth data available');
    }
  };
  const handleFrameSelect = (frameIndex) => {
    setCurrentFrame(frameIndex);
  };
  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };
  const handleSpeedChange = (speed) => {
    setPlaybackSpeed(speed);
  };
  const exportVisualization = async (format) => {
    if (!selectedResult) {
      onNotification('No result selected for export', 'error');
      return;
    }
    try {
      const response = await fetch(`/api/results/${selectedResult.id}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          format,
          visualization_type: visualizationType
        })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${selectedResult.algorithm_name}_${visualizationType}.${format}`;
        a.click();
        window.URL.revokeObjectURL(url);
        onNotification(`Visualization exported as ${format}`, 'success');
      }
    } catch (error) {
      onNotification('Error exporting visualization', 'error');
    }
  };
  const renderResultSelector = () => (
    <div style={{
      background: isDarkMode ? '#1a1a1a' : 'white',
      border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
      borderRadius: '12px',
      padding: '20px',
      marginBottom: '20px'
    }}>
      <h4 style={{ 
        margin: '0 0 16px 0', 
        color: isDarkMode ? '#e2e8f0' : '#1e293b',
        fontSize: '1rem',
        fontWeight: '600'
      }}>
        📊 Execution Results
      </h4>
      
      <select 
        value={selectedResult?.id || ''}
        onChange={(e) => {
          const result = executionResults.find(r => r.id === e.target.value);
          setSelectedResult(result);
        }}
        style={{
          width: '100%',
          padding: '12px 16px',
          border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
          borderRadius: '8px',
          background: isDarkMode ? '#334155' : 'white',
          color: isDarkMode ? '#e2e8f0' : '#1e293b',
          fontSize: '0.9rem',
          marginBottom: '16px'
        }}
      >
        <option value="">Select a result...</option>
        {executionResults.map(result => (
          <option key={result.id} value={result.id}>
            {result.algorithm_name} - {new Date(result.timestamp).toLocaleDateString()}
          </option>
        ))}
      </select>
      
      {selectedResult && (
        <div style={{
          background: isDarkMode ? '#334155' : '#f8fafc',
          borderRadius: '8px',
          padding: '16px'
        }}>
          <div style={{ marginBottom: '12px' }}>
            <div style={{ fontSize: '0.8rem', color: isDarkMode ? '#94a3b8' : '#64748b', marginBottom: '4px' }}>
              Algorithm
            </div>
            <div style={{ fontWeight: '600', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
              {selectedResult.algorithm_name}
            </div>
          </div>
          
          <div style={{ marginBottom: '12px' }}>
            <div style={{ fontSize: '0.8rem', color: isDarkMode ? '#94a3b8' : '#64748b', marginBottom: '4px' }}>
              Dataset
            </div>
            <div style={{ fontWeight: '600', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
              {selectedResult.dataset_name}
            </div>
          </div>
          
          <div>
            <div style={{ fontSize: '0.8rem', color: isDarkMode ? '#94a3b8' : '#64748b', marginBottom: '4px' }}>
              Status
            </div>
            <span style={{
              display: 'inline-block',
              padding: '4px 8px',
              borderRadius: '12px',
              fontSize: '0.8rem',
              fontWeight: '500',
              background: selectedResult.success ? '#22c55e' : '#ef4444',
              color: 'white'
            }}>
              {selectedResult.success ? '✓ Success' : '✕ Failed'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
  const renderVisualizationControls = () => (
    <div style={{
      background: isDarkMode ? '#1a1a1a' : 'white',
      border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
      borderRadius: '12px',
      padding: '20px',
      marginBottom: '20px'
    }}>
      <h4 style={{ 
        margin: '0 0 16px 0', 
        color: isDarkMode ? '#e2e8f0' : '#1e293b',
        fontSize: '1rem',
        fontWeight: '600'
      }}>
        🎛️ Visualization Controls
      </h4>
      
      <div style={{ marginBottom: '20px' }}>
        <div style={{ 
          fontSize: '0.9rem', 
          color: isDarkMode ? '#94a3b8' : '#64748b', 
          marginBottom: '8px',
          fontWeight: '500'
        }}>
          Visualization Type
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {[
            { id: 'trajectory', label: 'Trajectory', icon: '📈' },
            { id: 'pointcloud', label: 'Point Cloud', icon: '☁️' },
            { id: 'combined', label: 'Combined', icon: '🔗' }
          ].map(type => (
            <button 
              key={type.id}
              onClick={() => setVisualizationType(type.id)}
              style={{
                flex: 1,
                padding: '10px 12px',
                border: `1px solid ${visualizationType === type.id ? '#4f46e5' : (isDarkMode ? '#475569' : '#d1d5db')}`,
                background: visualizationType === type.id ? '#4f46e5' : 'transparent',
                color: visualizationType === type.id ? 'white' : (isDarkMode ? '#e2e8f0' : '#1e293b'),
                borderRadius: '6px',
                fontSize: '0.8rem',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px'
              }}
            >
              <span>{type.icon}</span>
              {type.label}
            </button>
          ))}
        </div>
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <div style={{ 
          fontSize: '0.9rem', 
          color: isDarkMode ? '#94a3b8' : '#64748b', 
          marginBottom: '8px',
          fontWeight: '500'
        }}>
          Playback Controls
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button 
            onClick={handlePlayPause}
            style={{
              padding: '8px 12px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              background: isDarkMode ? '#334155' : 'white',
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            {isPlaying ? '⏸️' : '▶️'}
          </button>
          <input 
            type="range"
            min="0.1"
            max="3"
            step="0.1"
            value={playbackSpeed}
            onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
            style={{ flex: 1 }}
          />
          <span style={{ 
            fontSize: '0.8rem', 
            color: isDarkMode ? '#94a3b8' : '#64748b',
            minWidth: '30px'
          }}>
            {playbackSpeed}x
          </span>
        </div>
      </div>
      
      <div>
        <div style={{ 
          fontSize: '0.9rem', 
          color: isDarkMode ? '#94a3b8' : '#64748b', 
          marginBottom: '8px',
          fontWeight: '500'
        }}>
          Export Options
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {[
            { format: 'png', label: 'PNG', icon: '🖼️' },
            { format: 'ply', label: 'PLY', icon: '📦' },
            { format: 'json', label: 'JSON', icon: '📄' }
          ].map(export_option => (
            <button 
              key={export_option.format}
              onClick={() => exportVisualization(export_option.format)}
              style={{
                flex: 1,
                padding: '8px 10px',
                border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                background: isDarkMode ? '#334155' : 'white',
                color: isDarkMode ? '#e2e8f0' : '#1e293b',
                borderRadius: '6px',
                fontSize: '0.8rem',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#4f46e5';
                e.currentTarget.style.color = 'white';
                e.currentTarget.style.borderColor = '#4f46e5';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = isDarkMode ? '#334155' : 'white';
                e.currentTarget.style.color = isDarkMode ? '#e2e8f0' : '#1e293b';
                e.currentTarget.style.borderColor = isDarkMode ? '#475569' : '#d1d5db';
              }}
            >
              <span>{export_option.icon}</span>
              {export_option.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
  const renderVisualization = () => {
    if (!selectedResult) {
      return (
        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '12px',
          padding: '60px 40px',
          textAlign: 'center',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '24px', opacity: 0.3 }}>📊</div>
          <h3 style={{ 
            margin: '0 0 12px 0', 
            color: isDarkMode ? '#e2e8f0' : '#1e293b',
            fontSize: '1.5rem',
            fontWeight: '600'
          }}>
            No Result Selected
          </h3>
          <p style={{ 
            margin: 0, 
            color: isDarkMode ? '#94a3b8' : '#64748b',
            fontSize: '1rem',
            lineHeight: '1.5'
          }}>
            Select an execution result from the sidebar to view its visualization
          </p>
        </div>
      );
    }
    
    const visualizationStyle = {
      background: isDarkMode ? '#1a1a1a' : 'white',
      border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
      borderRadius: '12px',
      padding: '20px',
      height: '100%',
      overflow: 'hidden'
    };
    
    switch (visualizationType) {
      case 'trajectory':
        return (
          <div style={visualizationStyle}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              marginBottom: '16px',
              paddingBottom: '12px',
              borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
            }}>
              <span style={{ fontSize: '1.2rem' }}>📈</span>
              <h4 style={{ 
                margin: 0, 
                color: isDarkMode ? '#e2e8f0' : '#1e293b',
                fontSize: '1.1rem',
                fontWeight: '600'
              }}>
                Trajectory Visualization
              </h4>
            </div>
            <TrajectoryVisualization 
              trajectoryData={trajectoryData}
              groundTruthData={groundTruthData}
              onFrameSelect={handleFrameSelect}
            />
          </div>
        );
      case 'pointcloud':
        return (
          <div style={visualizationStyle}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              marginBottom: '16px',
              paddingBottom: '12px',
              borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
            }}>
              <span style={{ fontSize: '1.2rem' }}>☁️</span>
              <h4 style={{ 
                margin: 0, 
                color: isDarkMode ? '#e2e8f0' : '#1e293b',
                fontSize: '1.1rem',
                fontWeight: '600'
              }}>
                Point Cloud Visualization
              </h4>
            </div>
            <PointCloudVisualization 
              pointCloudData={pointCloudData}
              trajectoryData={trajectoryData}
              currentPose={trajectoryData?.[currentFrame]?.pose}
              onPointSelect={(pointInfo) => {
                console.log('Point selected:', pointInfo);
              }}
            />
          </div>
        );
      case 'combined':
        return (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', height: '100%' }}>
            <div style={visualizationStyle}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                marginBottom: '16px',
                paddingBottom: '12px',
                borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
              }}>
                <span style={{ fontSize: '1rem' }}>📈</span>
                <h5 style={{ 
                  margin: 0, 
                  color: isDarkMode ? '#e2e8f0' : '#1e293b',
                  fontSize: '0.9rem',
                  fontWeight: '600'
                }}>
                  Trajectory
                </h5>
              </div>
              <TrajectoryVisualization 
                trajectoryData={trajectoryData}
                groundTruthData={groundTruthData}
                onFrameSelect={handleFrameSelect}
              />
            </div>
            <div style={visualizationStyle}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                marginBottom: '16px',
                paddingBottom: '12px',
                borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
              }}>
                <span style={{ fontSize: '1rem' }}>☁️</span>
                <h5 style={{ 
                  margin: 0, 
                  color: isDarkMode ? '#e2e8f0' : '#1e293b',
                  fontSize: '0.9rem',
                  fontWeight: '600'
                }}>
                  Point Cloud
                </h5>
              </div>
              <PointCloudVisualization 
                pointCloudData={pointCloudData}
                trajectoryData={trajectoryData}
                currentPose={trajectoryData?.[currentFrame]?.pose}
              />
            </div>
          </div>
        );
      default:
        return null;
    }
  };
  const renderMetricsPanel = () => {
    if (!selectedResult || !selectedResult.metrics) return null;
    return (
      <div style={{
        background: isDarkMode ? '#1a1a1a' : 'white',
        border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        borderRadius: '12px',
        padding: '20px'
      }}>
        <h4 style={{ 
          margin: '0 0 16px 0', 
          color: isDarkMode ? '#e2e8f0' : '#1e293b',
          fontSize: '1rem',
          fontWeight: '600'
        }}>
          📈 Performance Metrics
        </h4>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div style={{
            background: isDarkMode ? '#334155' : '#f8fafc',
            borderRadius: '8px',
            padding: '12px',
            textAlign: 'center'
          }}>
            <div style={{ 
              fontSize: '1.2rem', 
              fontWeight: '700', 
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              marginBottom: '4px'
            }}>
              {selectedResult.metrics.ate?.toFixed(4)}
            </div>
            <div style={{ 
              fontSize: '0.7rem', 
              color: isDarkMode ? '#94a3b8' : '#64748b',
              fontWeight: '500'
            }}>
              ATE (m)
            </div>
          </div>
          
          <div style={{
            background: isDarkMode ? '#334155' : '#f8fafc',
            borderRadius: '8px',
            padding: '12px',
            textAlign: 'center'
          }}>
            <div style={{ 
              fontSize: '1.2rem', 
              fontWeight: '700', 
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              marginBottom: '4px'
            }}>
              {selectedResult.metrics.rpe_trans?.toFixed(4)}
            </div>
            <div style={{ 
              fontSize: '0.7rem', 
              color: isDarkMode ? '#94a3b8' : '#64748b',
              fontWeight: '500'
            }}>
              RPE Trans (m)
            </div>
          </div>
          
          <div style={{
            background: isDarkMode ? '#334155' : '#f8fafc',
            borderRadius: '8px',
            padding: '12px',
            textAlign: 'center'
          }}>
            <div style={{ 
              fontSize: '1.2rem', 
              fontWeight: '700', 
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              marginBottom: '4px'
            }}>
              {selectedResult.metrics.rpe_rot?.toFixed(4)}
            </div>
            <div style={{ 
              fontSize: '0.7rem', 
              color: isDarkMode ? '#94a3b8' : '#64748b',
              fontWeight: '500'
            }}>
              RPE Rot (rad)
            </div>
          </div>
          
          <div style={{
            background: isDarkMode ? '#334155' : '#f8fafc',
            borderRadius: '8px',
            padding: '12px',
            textAlign: 'center'
          }}>
            <div style={{ 
              fontSize: '1.2rem', 
              fontWeight: '700', 
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              marginBottom: '4px'
            }}>
              {selectedResult.execution_time?.toFixed(2)}
            </div>
            <div style={{ 
              fontSize: '0.7rem', 
              color: isDarkMode ? '#94a3b8' : '#64748b',
              fontWeight: '500'
            }}>
              Time (s)
            </div>
          </div>
        </div>
      </div>
    );
  };
  const renderResultsTab = () => (
    <div style={{ padding: '24px', height: '100%' }}>
      <div style={{ display: 'flex', gap: '24px', height: '100%' }}>
        <div style={{ 
          flex: '0 0 320px',
          display: 'flex',
          flexDirection: 'column',
          gap: '0'
        }}>
          {renderResultSelector()}
          {renderVisualizationControls()}
          {renderMetricsPanel()}
        </div>
        <div style={{ 
          flex: 1,
          minHeight: '0',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {renderVisualization()}
        </div>
      </div>
    </div>
  );

  const renderComparisonTab = () => (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 16px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
          Algorithm Comparison
        </h3>
        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '12px',
          padding: '20px'
        }}>
          <h4 style={{ 
            margin: '0 0 16px 0', 
            color: isDarkMode ? '#e2e8f0' : '#1e293b',
            fontSize: '1rem',
            fontWeight: '600'
          }}>
            🔍 Select Results to Compare
          </h4>
          
          <div style={{ marginBottom: '16px' }}>
            <select 
              multiple
              style={{
                width: '100%',
                padding: '12px',
                border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                borderRadius: '8px',
                background: isDarkMode ? '#334155' : 'white',
                color: isDarkMode ? '#e2e8f0' : '#1e293b',
                minHeight: '150px',
                fontSize: '0.9rem'
              }}
            >
              {executionResults.map(result => (
                <option key={result.id} value={result.id}>
                  {result.algorithm_name} - {new Date(result.timestamp).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>
          
          <button
            style={{
              width: '100%',
              padding: '12px 16px',
              background: '#4f46e5',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: '600',
              transition: 'all 0.2s ease'
            }}
            onClick={() => {
              onNotification('Comparison analysis started', 'info');
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#4338ca';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#4f46e5';
            }}
          >
            🔄 Compare Selected Results
          </button>
        </div>
      </div>
      
      <div style={{
        background: isDarkMode ? '#1a1a1a' : 'white',
        border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        borderRadius: '8px',
        padding: '20px'
      }}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px', opacity: 0.3 }}>📊</div>
          <h4 style={{ margin: '0 0 8px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
            No Comparison Results
          </h4>
          <p style={{ margin: 0, color: isDarkMode ? '#94a3b8' : '#64748b' }}>
            Select multiple algorithm results to compare their performance
          </p>
        </div>
      </div>
    </div>
  );

  const renderAnalysisTab = () => (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ margin: '0 0 16px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
          Performance Analysis
        </h3>
        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <h4 style={{ 
            margin: '0 0 16px 0', 
            color: isDarkMode ? '#e2e8f0' : '#1e293b',
            fontSize: '1rem',
            fontWeight: '600'
          }}>
            📊 Analysis Generator
          </h4>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <select style={{
              flex: 1,
              padding: '12px 16px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '8px',
              background: isDarkMode ? '#334155' : 'white',
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              fontSize: '0.9rem'
            }}>
              <option>📈 Trajectory Error Analysis</option>
              <option>🎯 Feature Tracking Analysis</option>
              <option>🔄 Loop Closure Analysis</option>
              <option>⚡ Computational Performance</option>
            </select>
            <button
              style={{
                padding: '12px 20px',
                background: '#22c55e',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: '600',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#16a34a';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#22c55e';
              }}
            >
              🚀 Generate Analysis
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '8px',
          padding: '16px'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
            Error Distribution
          </h4>
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: isDarkMode ? '#94a3b8' : '#64748b' }}>Chart placeholder</span>
          </div>
        </div>

        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '8px',
          padding: '16px'
        }}>
          <h4 style={{ margin: '0 0 12px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
            Performance Metrics
          </h4>
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: isDarkMode ? '#94a3b8' : '#64748b' }}>Metrics placeholder</span>
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
          Visualization & Analysis
        </h1>
        <p style={{ margin: 0, color: isDarkMode ? '#94a3b8' : '#64748b', fontSize: '0.9rem' }}>
          Visualize results, compare algorithms, and analyze performance
        </p>
      </div>

      <div style={{
        display: 'flex',
        background: isDarkMode ? '#1a1a1a' : 'white',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
      }}>
        {[
          { id: 'results', label: 'Results Visualization', icon: '📈' },
          { id: 'comparison', label: 'Algorithm Comparison', icon: '⚖️' },
          { id: 'analysis', label: 'Performance Analysis', icon: '🔍' }
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
        {activeTab === 'results' && renderResultsTab()}
        {activeTab === 'comparison' && renderComparisonTab()}
        {activeTab === 'analysis' && renderAnalysisTab()}
      </div>
    </div>
  );
};
export default Visualization;