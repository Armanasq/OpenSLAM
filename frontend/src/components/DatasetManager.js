import React, { useState, useEffect } from 'react';
import DirectoryBrowserModal from './DirectoryBrowserModal';

const DatasetManager = ({ currentDataset, onDatasetSelect, onNotification, isDarkMode }) => {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState(currentDataset);
  const [datasetDetails, setDatasetDetails] = useState(null);
  const [previewFrame, setPreviewFrame] = useState(0);
  const [loadPath, setLoadPath] = useState('');
  const [showDirectoryBrowser, setShowDirectoryBrowser] = useState(false);
  useEffect(() => {
    loadDatasets();
  }, []);
  useEffect(() => {
    if (selectedDataset) {
      if (selectedDataset.id === 'demo_00') {
        // For demo dataset, use the dataset itself as details
        setDatasetDetails({ metadata: selectedDataset.metadata });
      } else {
        loadDatasetDetails(selectedDataset.id);
      }
    }
  }, [selectedDataset]);
  const loadDatasets = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/datasets');
      if (response.ok) {
        const data = await response.json();
        setDatasets(data);
        if (data.length > 0 && !selectedDataset) {
          setSelectedDataset(data[0]);
          onDatasetSelect(data[0]);
        }
      } else {
        onNotification('Failed to load datasets', 'error');
      }
    } catch (error) {
      onNotification('Error loading datasets', 'error');
    } finally {
      setLoading(false);
    }
  };
  const loadDatasetDetails = async (datasetId) => {
    try {
      const response = await fetch(`/api/datasets/${datasetId}/details`);
      if (response.ok) {
        const details = await response.json();
        setDatasetDetails(details);
      }
    } catch (error) {
      onNotification('Error loading dataset details', 'error');
    }
  };
  const handleDatasetSelect = (dataset) => {
    setSelectedDataset(dataset);
    onDatasetSelect(dataset);
    setPreviewFrame(0);
  };
  const validateDataset = async (datasetId) => {
    try {
      const response = await fetch(`/api/datasets/${datasetId}/validate`, {
        method: 'POST'
      });
      if (response.ok) {
        const result = await response.json();
        if (result.valid) {
          onNotification('Dataset validation successful', 'success');
        } else {
          onNotification(`Dataset validation failed: ${result.errors.join(', ')}`, 'error');
        }
      }
    } catch (error) {
      onNotification('Error validating dataset', 'error');
    }
  };
  const loadDemoDataset = () => {
    const demoDataset = {
      id: 'demo_00',
      name: 'KITTI Demo Dataset',
      format: 'KITTI',
      sequence_length: 4541,
      sensors: ['image_0', 'image_1', 'image_2', 'image_3', 'velodyne'],
      calibration: {
        P0: [7.188560e+02, 0.000000e+00, 6.071928e+02, 0.000000e+00, 0.000000e+00, 7.188560e+02, 1.852157e+02, 0.000000e+00, 0.000000e+00, 0.000000e+00, 1.000000e+00, 0.000000e+00],
        P1: [7.188560e+02, 0.000000e+00, 6.071928e+02, -3.861448e+02, 0.000000e+00, 7.188560e+02, 1.852157e+02, 0.000000e+00, 0.000000e+00, 0.000000e+00, 1.000000e+00, 0.000000e+00],
        P2: [7.188560e+02, 0.000000e+00, 6.071928e+02, 4.538225e+01, 0.000000e+00, 7.188560e+02, 1.852157e+02, -1.130887e-01, 0.000000e+00, 0.000000e+00, 1.000000e+00, 3.779761e-03],
        P3: [7.188560e+02, 0.000000e+00, 6.071928e+02, -3.372877e+02, 0.000000e+00, 7.188560e+02, 1.852157e+02, 2.369057e+00, 0.000000e+00, 0.000000e+00, 1.000000e+00, 4.915215e-03]
      },
      metadata: {
        has_ground_truth: true,
        path: '/demo/kitti/00'
      },
      created_at: new Date().toISOString()
    };
    
    setDatasets(prev => [...prev, demoDataset]);
    setSelectedDataset(demoDataset);
    onDatasetSelect(demoDataset);
    onNotification('Demo dataset loaded successfully', 'success');
  };

  const handleDirectorySelect = () => {
    setShowDirectoryBrowser(true);
  };

  const handleDirectorySelected = (path) => {
    setLoadPath(path);
    onNotification(`Selected directory: ${path}`, 'info');
  };



  const loadDatasetFromPath = async () => {
    if (!loadPath.trim()) {
      onNotification('Please select a dataset directory', 'error');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/datasets/load', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ path: loadPath })
      });
      if (response.ok) {
        const newDataset = await response.json();
        setDatasets(prev => [...prev, newDataset]);
        setSelectedDataset(newDataset);
        onDatasetSelect(newDataset);
        onNotification(`Dataset ${newDataset.name} loaded successfully`, 'success');
        setLoadPath('');
      } else {
        const error = await response.json();
        const errorMessage = error.detail?.message || error.detail || error.message || 'Unknown error';
        onNotification(`Failed to load dataset: ${errorMessage}`, 'error');
      }
    } catch (error) {
      onNotification('Error connecting to backend. Make sure the backend server is running.', 'error');
      console.error('Dataset loading error:', error);
    } finally {
      setLoading(false);
    }
  };
  const renderDatasetList = () => (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '24px',
        paddingBottom: '16px',
        borderBottom: '2px solid #ecf0f1'
      }}>
        <div>
          <h3 style={{ margin: '0 0 4px 0', color: '#2c3e50', fontSize: '1.4rem' }}>Available Datasets</h3>
          <p style={{ margin: '0', color: '#7f8c8d', fontSize: '0.9rem' }}>
            {datasets.length} dataset{datasets.length !== 1 ? 's' : ''} loaded
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <button 
            onClick={handleDirectorySelect}
            style={{ 
              padding: '8px 16px', 
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px', 
              cursor: 'pointer',
              fontSize: '0.9rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              fontWeight: '500'
            }}
          >
            📁 Browse Directories
          </button>
          
          <input
            type="text"
            value={loadPath}
            onChange={(e) => setLoadPath(e.target.value)}
            placeholder="Enter dataset path (e.g., /home/arman/project/SLAM/v1/data/00)"
            style={{
              padding: '8px 12px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '6px',
              background: isDarkMode ? '#334155' : 'white',
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              fontSize: '0.9rem',
              minWidth: '350px',
              fontFamily: 'monospace'
            }}
          />
          
          <button 
            onClick={loadDatasetFromPath}
            disabled={loading || !loadPath.trim()}
            style={{ 
              padding: '8px 16px', 
              background: loading || !loadPath.trim() 
                ? (isDarkMode ? '#475569' : '#d1d5db')
                : '#4f46e5',
              color: 'white', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: loading || !loadPath.trim() ? 'not-allowed' : 'pointer',
              fontWeight: '500',
              fontSize: '0.9rem'
            }}
          >
            {loading ? 'Loading...' : 'Load Dataset'}
          </button>
          <button 
            onClick={loadDemoDataset} 
            style={{ 
              padding: '10px 16px', 
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '8px', 
              cursor: 'pointer',
              fontWeight: '500',
              fontSize: '0.9rem',
              boxShadow: '0 2px 8px rgba(240, 147, 251, 0.3)',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => e.target.style.transform = 'translateY(-1px)'}
            onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
          >
            🎮 Load Demo
          </button>
        </div>
      </div>
      
      {loading ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px', 
          color: '#7f8c8d',
          background: '#f8f9fa',
          borderRadius: '12px',
          border: '2px dashed #dee2e6'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>⏳</div>
          <div style={{ fontSize: '1.1rem', fontWeight: '500' }}>Loading datasets...</div>
        </div>
      ) : datasets.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px', 
          color: '#7f8c8d',
          background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
          borderRadius: '12px',
          border: '2px dashed #dee2e6'
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '20px', opacity: 0.3 }}>📊</div>
          <h3 style={{ margin: '0 0 12px 0', color: '#2c3e50', fontSize: '1.3rem' }}>No Datasets Loaded</h3>
          <p style={{ margin: '0 0 20px 0', fontSize: '0.95rem', lineHeight: '1.5' }}>
            Get started by loading a demo dataset or importing your own KITTI dataset
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button 
              onClick={loadDemoDataset}
              style={{
                padding: '12px 20px',
                background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '500',
                fontSize: '0.9rem',
                boxShadow: '0 4px 12px rgba(79, 172, 254, 0.3)'
              }}
            >
              🚀 Try Demo Dataset
            </button>
            <button 
              onClick={loadDatasetFromPath}
              style={{
                padding: '12px 20px',
                background: 'transparent',
                color: '#667eea',
                border: '2px solid #667eea',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '500',
                fontSize: '0.9rem'
              }}
            >
              📂 Load Your Dataset
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '12px' }}>
          {datasets.map(dataset => (
            <div 
              key={dataset.id} 
              style={{
                background: selectedDataset?.id === dataset.id 
                  ? 'linear-gradient(135deg, #ebf3fd 0%, #f0f7ff 100%)' 
                  : 'white',
                border: `2px solid ${selectedDataset?.id === dataset.id ? '#667eea' : '#e9ecef'}`,
                borderRadius: '12px',
                padding: '20px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: selectedDataset?.id === dataset.id 
                  ? '0 4px 20px rgba(102, 126, 234, 0.15)' 
                  : '0 2px 8px rgba(0,0,0,0.05)',
                position: 'relative',
                overflow: 'hidden'
              }}
              onClick={() => handleDatasetSelect(dataset)}
              onMouseOver={(e) => {
                if (selectedDataset?.id !== dataset.id) {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 4px 16px rgba(0,0,0,0.1)';
                }
              }}
              onMouseOut={(e) => {
                if (selectedDataset?.id !== dataset.id) {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
                }
              }}
            >
              {selectedDataset?.id === dataset.id && (
                <div style={{
                  position: 'absolute',
                  top: 0,
                  right: 0,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  padding: '4px 12px',
                  borderBottomLeftRadius: '8px',
                  fontSize: '0.7rem',
                  fontWeight: '600'
                }}>
                  SELECTED
                </div>
              )}
              
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'flex-start', 
                marginBottom: '16px' 
              }}>
                <div>
                  <h4 style={{ 
                    margin: '0 0 8px 0', 
                    color: '#2c3e50', 
                    fontSize: '1.2rem',
                    fontWeight: '600'
                  }}>
                    {dataset.name}
                  </h4>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    <span style={{ 
                      background: '#e3f2fd', 
                      color: '#1976d2', 
                      padding: '3px 8px', 
                      borderRadius: '12px', 
                      fontSize: '0.75rem',
                      fontWeight: '500'
                    }}>
                      {dataset.format}
                    </span>
                    {dataset.metadata?.has_ground_truth && (
                      <span style={{ 
                        background: '#e8f5e8', 
                        color: '#2e7d32', 
                        padding: '3px 8px', 
                        borderRadius: '12px', 
                        fontSize: '0.75rem',
                        fontWeight: '500'
                      }}>
                        ✓ GT
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 1fr', 
                gap: '12px',
                marginBottom: '12px'
              }}>
                <div style={{ 
                  background: 'rgba(102, 126, 234, 0.1)', 
                  padding: '12px', 
                  borderRadius: '8px',
                  textAlign: 'center'
                }}>
                  <div style={{ 
                    fontSize: '1.3rem', 
                    fontWeight: 'bold', 
                    color: '#667eea',
                    marginBottom: '2px'
                  }}>
                    {dataset.sequence_length?.toLocaleString() || '0'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#7f8c8d', fontWeight: '500' }}>
                    Frames
                  </div>
                </div>
                <div style={{ 
                  background: 'rgba(240, 147, 251, 0.1)', 
                  padding: '12px', 
                  borderRadius: '8px',
                  textAlign: 'center'
                }}>
                  <div style={{ 
                    fontSize: '1.3rem', 
                    fontWeight: 'bold', 
                    color: '#f093fb',
                    marginBottom: '2px'
                  }}>
                    {dataset.sensors?.length || 0}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#7f8c8d', fontWeight: '500' }}>
                    Sensors
                  </div>
                </div>
              </div>
              
              <div style={{ 
                display: 'flex', 
                gap: '4px', 
                flexWrap: 'wrap',
                justifyContent: 'center'
              }}>
                {dataset.sensors?.slice(0, 4).map(sensor => (
                  <span key={sensor} style={{ 
                    background: '#f8f9fa', 
                    color: '#6c757d', 
                    padding: '2px 6px', 
                    borderRadius: '4px', 
                    fontSize: '0.7rem',
                    fontWeight: '500',
                    border: '1px solid #e9ecef'
                  }}>
                    {sensor.replace('_', ' ')}
                  </span>
                ))}
                {dataset.sensors?.length > 4 && (
                  <span style={{ 
                    color: '#7f8c8d', 
                    fontSize: '0.7rem',
                    fontWeight: '500'
                  }}>
                    +{dataset.sensors.length - 4} more
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
  const renderDatasetDetails = () => {
    if (!selectedDataset) {
      return (
        <div>
          <div style={{ 
            textAlign: 'center', 
            padding: '60px 20px', 
            color: '#7f8c8d',
            background: '#f8f9fa',
            borderRadius: '12px',
            border: '2px dashed #dee2e6'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px', opacity: 0.3 }}>📊</div>
            <h3 style={{ margin: '0 0 8px 0', color: '#2c3e50', fontSize: '1.2rem' }}>No Dataset Selected</h3>
            <p style={{ margin: '0', fontSize: '0.9rem' }}>Select a dataset from the list to view its details and preview frames.</p>
          </div>
        </div>
      );
    }
    
    if (!datasetDetails) {
      return (
        <div>
          <div style={{ 
            textAlign: 'center', 
            padding: '40px', 
            color: '#7f8c8d',
            background: '#f8f9fa',
            borderRadius: '8px'
          }}>
            <div style={{ fontSize: '2rem', marginBottom: '12px' }}>⏳</div>
            Loading dataset details...
          </div>
        </div>
      );
    }
    
    return (
      <div>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: '24px',
          paddingBottom: '16px',
          borderBottom: '2px solid #ecf0f1'
        }}>
          <div>
            <h3 style={{ margin: '0 0 4px 0', color: '#2c3e50', fontSize: '1.4rem' }}>{selectedDataset.name}</h3>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ 
                background: '#e3f2fd', 
                color: '#1976d2', 
                padding: '2px 8px', 
                borderRadius: '12px', 
                fontSize: '0.75rem',
                fontWeight: '500'
              }}>
                {selectedDataset.format}
              </span>
              <span style={{ 
                background: '#f3e5f5', 
                color: '#7b1fa2', 
                padding: '2px 8px', 
                borderRadius: '12px', 
                fontSize: '0.75rem',
                fontWeight: '500'
              }}>
                {selectedDataset.sequence_length?.toLocaleString()} frames
              </span>
              {selectedDataset.metadata?.has_ground_truth && (
                <span style={{ 
                  background: '#e8f5e8', 
                  color: '#2e7d32', 
                  padding: '2px 8px', 
                  borderRadius: '12px', 
                  fontSize: '0.75rem',
                  fontWeight: '500'
                }}>
                  ✓ Ground Truth
                </span>
              )}
            </div>
          </div>
          <button 
            onClick={() => validateDataset(selectedDataset.id)}
            style={{
              padding: '8px 16px',
              background: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '500',
              fontSize: '0.9rem'
            }}
          >
            Validate
          </button>
        </div>

        {/* Dataset Stats Cards */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', 
          gap: '12px', 
          marginBottom: '24px' 
        }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
            color: 'white', 
            padding: '16px', 
            borderRadius: '8px', 
            textAlign: 'center' 
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '4px' }}>
              {selectedDataset.sequence_length?.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>Total Frames</div>
          </div>
          <div style={{ 
            background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', 
            color: 'white', 
            padding: '16px', 
            borderRadius: '8px', 
            textAlign: 'center' 
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '4px' }}>
              {selectedDataset.sensors?.length || 0}
            </div>
            <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>Sensors</div>
          </div>
          <div style={{ 
            background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', 
            color: 'white', 
            padding: '16px', 
            borderRadius: '8px', 
            textAlign: 'center' 
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '4px' }}>
              {selectedDataset.sensors?.filter(s => s.startsWith('image')).length || 0}
            </div>
            <div style={{ fontSize: '0.8rem', opacity: 0.9 }}>Cameras</div>
          </div>
        </div>

        {/* Dataset Information */}
        <div style={{ 
          background: 'white', 
          border: '1px solid #e9ecef', 
          borderRadius: '8px', 
          padding: '20px', 
          marginBottom: '20px' 
        }}>
          <h4 style={{ margin: '0 0 16px 0', color: '#2c3e50', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📋</span> Dataset Information
          </h4>
          <div style={{ display: 'grid', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #f8f9fa' }}>
              <span style={{ color: '#7f8c8d', fontWeight: '500' }}>Format:</span>
              <span style={{ color: '#2c3e50', fontWeight: '500' }}>{selectedDataset.format}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #f8f9fa' }}>
              <span style={{ color: '#7f8c8d', fontWeight: '500' }}>Sensors:</span>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {selectedDataset.sensors?.map(sensor => (
                  <span key={sensor} style={{ 
                    background: '#e3f2fd', 
                    color: '#1976d2', 
                    padding: '2px 6px', 
                    borderRadius: '4px', 
                    fontSize: '0.75rem',
                    fontWeight: '500'
                  }}>
                    {sensor.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0' }}>
              <span style={{ color: '#7f8c8d', fontWeight: '500' }}>Path:</span>
              <span style={{ 
                fontFamily: 'monospace', 
                fontSize: '0.8rem', 
                background: '#f8f9fa', 
                padding: '2px 6px', 
                borderRadius: '3px',
                color: '#2c3e50'
              }}>
                {selectedDataset.metadata?.path || 'Demo dataset'}
              </span>
            </div>
          </div>
        </div>

        {/* Calibration */}
        <div style={{ 
          background: 'white', 
          border: '1px solid #e9ecef', 
          borderRadius: '8px', 
          padding: '20px', 
          marginBottom: '20px' 
        }}>
          <h4 style={{ margin: '0 0 16px 0', color: '#2c3e50', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🎯</span> Calibration
          </h4>
          <div style={{ display: 'grid', gap: '8px' }}>
            {selectedDataset.calibration && Object.entries(selectedDataset.calibration).length > 0 ? 
              Object.entries(selectedDataset.calibration).map(([key, values]) => (
                <div key={key} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center', 
                  padding: '6px 0',
                  borderBottom: '1px solid #f8f9fa'
                }}>
                  <span style={{ color: '#7f8c8d', fontWeight: '500', minWidth: '40px' }}>{key}:</span>
                  <span style={{ 
                    fontFamily: 'monospace', 
                    fontSize: '0.8rem', 
                    color: '#2c3e50',
                    background: '#f8f9fa',
                    padding: '2px 6px',
                    borderRadius: '3px'
                  }}>
                    [{values.slice(0, 4).map(v => v.toFixed(3)).join(', ')}...]
                  </span>
                </div>
              )) : (
                <div style={{ 
                  textAlign: 'center', 
                  color: '#7f8c8d', 
                  padding: '20px',
                  fontStyle: 'italic'
                }}>
                  No calibration data available
                </div>
              )
            }
          </div>
        </div>

        {/* Frame Preview */}
        <div style={{ 
          background: 'white', 
          border: '1px solid #e9ecef', 
          borderRadius: '8px', 
          padding: '20px' 
        }}>
          <h4 style={{ margin: '0 0 16px 0', color: '#2c3e50', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🎬</span> Frame Preview
          </h4>
          <div style={{ marginBottom: '16px' }}>
            <input 
              type="range" 
              min="0" 
              max={selectedDataset.sequence_length - 1}
              value={previewFrame}
              onChange={(e) => setPreviewFrame(parseInt(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                background: '#e9ecef',
                outline: 'none',
                marginBottom: '12px',
                cursor: 'pointer'
              }}
            />
            <div style={{ 
              textAlign: 'center', 
              fontFamily: 'monospace', 
              color: '#7f8c8d',
              fontSize: '0.9rem',
              background: '#f8f9fa',
              padding: '8px',
              borderRadius: '4px'
            }}>
              Frame <strong style={{ color: '#667eea' }}>{previewFrame}</strong> / {selectedDataset.sequence_length - 1}
            </div>
          </div>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '12px' 
          }}>
            {selectedDataset.sensors?.filter(s => s.startsWith('image')).map(sensor => (
              <div key={sensor} style={{ textAlign: 'center' }}>
                <div style={{ 
                  marginBottom: '8px', 
                  fontWeight: '500', 
                  color: '#2c3e50', 
                  textTransform: 'uppercase', 
                  fontSize: '0.8rem',
                  background: '#f8f9fa',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  display: 'inline-block'
                }}>
                  {sensor.replace('_', ' ')}
                </div>
                <div style={{ 
                  border: '2px solid #e9ecef', 
                  borderRadius: '8px', 
                  overflow: 'hidden',
                  background: '#f8f9fa',
                  minHeight: '120px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <img 
                    src={`/api/datasets/${selectedDataset.id}/frame/${previewFrame}/${sensor}`}
                    alt={`${sensor} frame ${previewFrame}`}
                    style={{ 
                      width: '100%', 
                      height: 'auto', 
                      maxHeight: '150px',
                      objectFit: 'cover'
                    }}
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.parentElement.innerHTML = '<div style="color: #7f8c8d; font-size: 0.8rem;">Image not available</div>';
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };
  return (
    <div style={{ 
      padding: '24px', 
      background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
      minHeight: '100vh'
    }}>
      <div style={{ 
        marginBottom: '32px',
        textAlign: 'center',
        background: 'white',
        padding: '24px',
        borderRadius: '16px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
      }}>
        <h2 style={{ 
          margin: '0 0 8px 0', 
          color: '#2c3e50', 
          fontSize: '2rem',
          fontWeight: '700',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Dataset Management
        </h2>
        <p style={{ 
          margin: '0', 
          color: '#7f8c8d', 
          fontSize: '1.1rem',
          fontWeight: '400'
        }}>
          Load, validate, and preview SLAM datasets for algorithm development
        </p>
      </div>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: window.innerWidth > 1200 ? '1fr 1.2fr' : '1fr',
        gap: '24px',
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        <div style={{ 
          background: 'white', 
          borderRadius: '16px', 
          padding: '24px', 
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          border: '1px solid rgba(255,255,255,0.2)'
        }}>
          {renderDatasetList()}
        </div>
        <div style={{ 
          background: 'white', 
          borderRadius: '16px', 
          padding: '24px', 
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          border: '1px solid rgba(255,255,255,0.2)'
        }}>
          {renderDatasetDetails()}
        </div>
      </div>

      <DirectoryBrowserModal
        isOpen={showDirectoryBrowser}
        onClose={() => setShowDirectoryBrowser(false)}
        onSelectDirectory={handleDirectorySelected}
        isDarkMode={isDarkMode}
      />
    </div>
  );
};
export default DatasetManager;