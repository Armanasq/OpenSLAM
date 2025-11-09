import React, { useState, useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';

const DatasetPreview = ({ dataset, onNotification }) => {
  const [groundTruth, setGroundTruth] = useState(null);
  const [selectedFrame, setSelectedFrame] = useState(0);
  const [lidarData, setLidarData] = useState(null);
  const [lidarResolution, setLidarResolution] = useState(10000);
  const [viewMode, setViewMode] = useState('trajectory');
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(100);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [cameraState, setCameraState] = useState({});
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const playIntervalRef = useRef(null);

  useEffect(() => {
    if (dataset && dataset.id) {
      loadGroundTruth();
    }
  }, [dataset]);

  useEffect(() => {
    if (dataset && dataset.id && (viewMode === 'lidar' || viewMode === 'combined')) {
      loadLidarData(selectedFrame);
    }
  }, [selectedFrame, dataset, viewMode, lidarResolution]);
  
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    setIsDarkMode(savedTheme === 'dark');
  }, []);
  
  useEffect(() => {
    if (isPlaying && dataset) {
      playIntervalRef.current = setInterval(() => {
        setSelectedFrame(prev => {
          if (prev >= dataset.sequence_length - 1) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, playSpeed);
    } else {
      clearInterval(playIntervalRef.current);
    }
    return () => clearInterval(playIntervalRef.current);
  }, [isPlaying, playSpeed, dataset]);

  const loadGroundTruth = async () => {
    if (!dataset?.metadata?.has_ground_truth) return;
    setLoading(true);
    const response = await fetch(`/api/datasets/${dataset.id}/ground-truth`);
    if (response.ok) {
      const data = await response.json();
      setGroundTruth(data.trajectory);
    }
    setLoading(false);
  };

  const loadLidarData = async (frameId) => {
    const lidarSensor = dataset?.sensors?.find(s => s === 'velodyne');
    if (!lidarSensor) {
      return;
    }
    const response = await fetch(`/api/datasets/${dataset.id}/lidar/${frameId}?resolution=${lidarResolution}`);
    if (response.ok) {
      const data = await response.json();
      setLidarData(data);
    }
  };

  const getPlotTheme = () => ({
    paper_bgcolor: isDarkMode ? '#0f0f0f' : '#ffffff',
    plot_bgcolor: isDarkMode ? '#1a1a1a' : '#fafafa',
    font: { color: isDarkMode ? '#e0e0e0' : '#2c3e50' }
  });

  const renderTrajectoryPlot = () => {
    if (!groundTruth) return null;
    const x = groundTruth.map(point => point.position[0]);
    const y = groundTruth.map(point => point.position[1]);
    const z = groundTruth.map(point => point.position[2]);
    const selectedPoint = groundTruth[selectedFrame];
    const theme = getPlotTheme();
    
    return (
      <Plot
        data={[
          {
            x: x,
            y: y,
            z: z,
            mode: 'lines+markers',
            type: 'scatter3d',
            name: 'Trajectory',
            line: { color: isDarkMode ? '#00d4ff' : '#4f46e5', width: 3 },
            marker: { size: 1.5, color: isDarkMode ? '#00d4ff' : '#4f46e5' }
          },
          selectedPoint ? {
            x: [selectedPoint.position[0]],
            y: [selectedPoint.position[1]],
            z: [selectedPoint.position[2]],
            mode: 'markers',
            type: 'scatter3d',
            name: 'Current Position',
            marker: { 
              size: 8, 
              color: isDarkMode ? '#ff6b6b' : '#ef4444', 
              symbol: 'diamond',
              line: { width: 2, color: isDarkMode ? '#ffffff' : '#000000' }
            }
          } : null
        ].filter(Boolean)}
        layout={{
          scene: {
            xaxis: { 
              title: 'X (m)', 
              titlefont: { color: theme.font.color, size: 11 },
              tickfont: { color: theme.font.color, size: 9 },
              gridcolor: isDarkMode ? '#333333' : '#e5e7eb',
              showspikes: false
            },
            yaxis: { 
              title: 'Y (m)', 
              titlefont: { color: theme.font.color, size: 11 },
              tickfont: { color: theme.font.color, size: 9 },
              gridcolor: isDarkMode ? '#333333' : '#e5e7eb',
              showspikes: false
            },
            zaxis: { 
              title: 'Z (m)', 
              titlefont: { color: theme.font.color, size: 11 },
              tickfont: { color: theme.font.color, size: 9 },
              gridcolor: isDarkMode ? '#333333' : '#e5e7eb',
              showspikes: false
            },
            aspectmode: 'manual',
            aspectratio: { x: 2, y: 2, z: 0.3 },
            camera: cameraState.trajectory || { 
              eye: { x: 1.8, y: 1.8, z: 0.8 },
              center: { x: 0, y: 0, z: 0 }
            },
            bgcolor: theme.plot_bgcolor
          },
          showlegend: false,
          uirevision: 'trajectory',
          margin: { l: 0, r: 0, b: 0, t: 0 },
          ...theme
        }}
        style={{ width: '100%', height: '100%' }}
        config={{ 
          displayModeBar: false,
          responsive: true, 
          displaylogo: false
        }}
        onRelayout={(eventData) => {
          if (eventData['scene.camera']) {
            setCameraState(prev => ({
              ...prev,
              trajectory: eventData['scene.camera']
            }));
          }
        }}
      />
    );
  };

  const renderLidarPlot = () => {
    if (!lidarData || !lidarData.x || lidarData.x.length === 0) return null;
    const theme = getPlotTheme();
    
    const filteredX = [];
    const filteredY = [];
    const filteredZ = [];
    const filteredIntensity = [];
    
    for (let i = 0; i < lidarData.x.length; i++) {
      const x = lidarData.x[i];
      const y = lidarData.y[i];
      const z = lidarData.z[i];
      const distance = Math.sqrt(x*x + y*y + z*z);
      
      if (distance > 1.0 && distance < 80.0 && z > -3.0 && z < 5.0) {
        filteredX.push(x);
        filteredY.push(y);
        filteredZ.push(z);
        filteredIntensity.push(lidarData.intensity ? lidarData.intensity[i] : 50);
      }
    }
    
    return (
      <Plot
        data={[
          {
            x: filteredX,
            y: filteredY,
            z: filteredZ,
            mode: 'markers',
            type: 'scatter3d',
            name: 'Point Cloud',
            marker: {
              size: 1,
              color: filteredIntensity,
              colorscale: 'Viridis',
              showscale: true,
              colorbar: { 
                title: {
                  text: 'Intensity',
                  font: { color: theme.font.color, size: 10, family: 'Inter, -apple-system, sans-serif' },
                  side: 'right'
                },
                tickfont: { color: theme.font.color, size: 8, family: 'Inter, -apple-system, sans-serif' },
                bgcolor: isDarkMode ? 'rgba(26, 26, 26, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                bordercolor: isDarkMode ? '#475569' : '#d1d5db',
                borderwidth: 1,
                thickness: 12,
                len: 0.6,
                x: 1.02,
                xpad: 5,
                ypad: 10,
                outlinecolor: isDarkMode ? '#475569' : '#d1d5db',
                outlinewidth: 1
              },
              opacity: 0.8,
              line: { width: 0 }
            }
          }
        ]}
        layout={{
          scene: {
            xaxis: { 
              title: 'X (m)', 
              titlefont: { color: theme.font.color, size: 11 },
              tickfont: { color: theme.font.color, size: 9 },
              gridcolor: isDarkMode ? '#333333' : '#e5e7eb',
              showspikes: false
            },
            yaxis: { 
              title: 'Y (m)', 
              titlefont: { color: theme.font.color, size: 11 },
              tickfont: { color: theme.font.color, size: 9 },
              gridcolor: isDarkMode ? '#333333' : '#e5e7eb',
              showspikes: false
            },
            zaxis: { 
              title: 'Z (m)', 
              titlefont: { color: theme.font.color, size: 11 },
              tickfont: { color: theme.font.color, size: 9 },
              gridcolor: isDarkMode ? '#333333' : '#e5e7eb',
              showspikes: false
            },
            aspectmode: 'data',
            camera: cameraState.lidar || { 
              eye: { x: 1.5, y: 1.5, z: 0.8 },
              center: { x: 0, y: 0, z: 0 }
            },
            bgcolor: theme.plot_bgcolor
          },
          showlegend: false,
          uirevision: 'lidar',
          margin: { l: 0, r: 0, b: 0, t: 0 },
          ...theme
        }}
        style={{ width: '100%', height: '100%' }}
        config={{ 
          displayModeBar: false,
          responsive: true, 
          displaylogo: false
        }}
        onRelayout={(eventData) => {
          if (eventData['scene.camera']) {
            setCameraState(prev => ({
              ...prev,
              lidar: eventData['scene.camera']
            }));
          }
        }}
      />
    );
  };

  const renderCombinedView = () => {
    if (!groundTruth || !lidarData) return null;
    const theme = getPlotTheme();

    const transformLidarToWorld = (lidarX, lidarY, lidarZ, pose) => {
      if (!lidarX || !lidarY || !lidarZ || lidarX.length === 0) {
        return {worldX: [], worldY: [], worldZ: [], filteredIntensity: []};
      }
      const R = pose.pose;
      const worldX = [];
      const worldY = [];
      const worldZ = [];
      const filteredIntensity = [];
      for (let i = 0; i < lidarX.length; i++) {
        const lx = lidarX[i];
        const ly = lidarY[i];
        const lz = lidarZ[i];
        const distance = Math.sqrt(lx*lx + ly*ly + lz*lz);
        if (distance > 1.0 && distance < 80.0 && lz > -3.0 && lz < 5.0) {
          const cx = -ly;
          const cy = -lz;
          const cz = lx;
          const wx_cam = R[0][0] * cx + R[0][1] * cy + R[0][2] * cz + pose.position[0];
          const wy_cam = R[1][0] * cx + R[1][1] * cy + R[1][2] * cz + pose.position[1];
          const wz_cam = R[2][0] * cx + R[2][1] * cy + R[2][2] * cz + pose.position[2];
          worldX.push(wz_cam);
          worldY.push(-wx_cam);
          worldZ.push(-wy_cam);
          filteredIntensity.push(lidarData.intensity ? lidarData.intensity[i] : 50);
        }
      }
      return {worldX, worldY, worldZ, filteredIntensity};
    };
    
    const trajectoryTrace = {
      x: groundTruth.map(point => point.position[2]),
      y: groundTruth.map(point => -point.position[0]),
      z: groundTruth.map(point => -point.position[1]),
      mode: 'lines+markers',
      type: 'scatter3d',
      name: 'Trajectory',
      line: {color: isDarkMode ? '#00d4ff' : '#4f46e5', width: 3},
      marker: {size: 1.5, color: isDarkMode ? '#00d4ff' : '#4f46e5'},
      opacity: 0.9
    };

    const currentPoseTrace = {
      x: [groundTruth[selectedFrame].position[2]],
      y: [-groundTruth[selectedFrame].position[0]],
      z: [-groundTruth[selectedFrame].position[1]],
      mode: 'markers',
      type: 'scatter3d',
      name: 'Current Position',
      marker: {size: 8, color: isDarkMode ? '#ff6b6b' : '#ef4444', symbol: 'diamond', line: {width: 2, color: isDarkMode ? '#ffffff' : '#000000'}}
    };

    const currentPose = groundTruth[selectedFrame];
    const { worldX, worldY, worldZ, filteredIntensity } = transformLidarToWorld(
      lidarData.x, 
      lidarData.y, 
      lidarData.z, 
      currentPose
    );
    
    const lidarTrace = {
      x: worldX,
      y: worldY,
      z: worldZ,
      mode: 'markers',
      type: 'scatter3d',
      name: 'Point Cloud',
      marker: {
        size: 0.5,
        color: filteredIntensity,
        colorscale: 'Viridis',
        opacity: 0.4,
        showscale: true,
        colorbar: { 
          title: {
            text: 'Intensity',
            font: { color: theme.font.color, size: 10, family: 'Inter, -apple-system, sans-serif' },
            side: 'right'
          },
          tickfont: { color: theme.font.color, size: 8, family: 'Inter, -apple-system, sans-serif' },
          bgcolor: isDarkMode ? 'rgba(26, 26, 26, 0.95)' : 'rgba(255, 255, 255, 0.95)',
          bordercolor: isDarkMode ? '#475569' : '#d1d5db',
          borderwidth: 1,
          x: 1.02,
          thickness: 12,
          len: 0.6,
          xpad: 5,
          ypad: 10,
          outlinecolor: isDarkMode ? '#475569' : '#d1d5db',
          outlinewidth: 1
        },
        line: { width: 0 }
      }
    };
    
    const arrowLength = 5;
    const R = currentPose.pose;
    const forwardX = R[0][2] * arrowLength;
    const forwardY = R[1][2] * arrowLength;
    const forwardZ = R[2][2] * arrowLength;
    const vehicleOrientationTrace = {
      x: [currentPose.position[2], currentPose.position[2] + forwardZ],
      y: [-currentPose.position[0], -currentPose.position[0] - forwardX],
      z: [-currentPose.position[1], -currentPose.position[1] - forwardY],
      mode: 'lines+markers',
      type: 'scatter3d',
      name: 'Direction',
      line: {color: isDarkMode ? '#ffd700' : '#f59e0b', width: 6},
      marker: {size: [3, 8], color: [isDarkMode ? '#ffd700' : '#f59e0b', isDarkMode ? '#ffd700' : '#f59e0b'], symbol: ['circle', 'diamond']},
      showlegend: true
    };

    return (
      <Plot
        data={[lidarTrace, trajectoryTrace, currentPoseTrace, vehicleOrientationTrace]}
        layout={{
          scene: {
            xaxis: { 
              title: 'X (m)', 
              titlefont: { color: theme.font.color, size: 11 },
              tickfont: { color: theme.font.color, size: 9 },
              gridcolor: isDarkMode ? '#333333' : '#e5e7eb',
              showspikes: false
            },
            yaxis: { 
              title: 'Y (m)', 
              titlefont: { color: theme.font.color, size: 11 },
              tickfont: { color: theme.font.color, size: 9 },
              gridcolor: isDarkMode ? '#333333' : '#e5e7eb',
              showspikes: false
            },
            zaxis: { 
              title: 'Z (m)', 
              titlefont: { color: theme.font.color, size: 11 },
              tickfont: { color: theme.font.color, size: 9 },
              gridcolor: isDarkMode ? '#333333' : '#e5e7eb',
              showspikes: false
            },
            aspectmode: 'data',
            camera: cameraState.combined || { 
              eye: { x: 1.5, y: 1.5, z: 0.8 },
              center: { x: 0, y: 0, z: 0 }
            },
            bgcolor: theme.plot_bgcolor
          },
          legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: isDarkMode ? 'rgba(26, 26, 26, 0.95)' : 'rgba(255, 255, 255, 0.95)',
            bordercolor: isDarkMode ? '#475569' : '#d1d5db',
            borderwidth: 1,
            font: { size: 9, color: theme.font.color, family: 'Inter, -apple-system, sans-serif' },
            orientation: 'v',
            itemsizing: 'constant',
            itemwidth: 30,
            tracegroupgap: 3,
            xanchor: 'left',
            yanchor: 'top'
          },
          uirevision: 'combined',
          margin: { l: 0, r: 0, b: 0, t: 0 },
          ...theme
        }}
        style={{ width: '100%', height: '100%' }}
        config={{ 
          displayModeBar: false,
          responsive: true, 
          displaylogo: false
        }}
        onRelayout={(eventData) => {
          if (eventData['scene.camera']) {
            setCameraState(prev => ({
              ...prev,
              combined: eventData['scene.camera']
            }));
          }
        }}
      />
    );
  };

  if (!dataset) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: isDarkMode 
          ? 'linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%)' 
          : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        color: isDarkMode ? '#e0e0e0' : '#64748b'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px', opacity: 0.4 }}>📊</div>
          <h2 style={{ margin: '0 0 8px 0', fontSize: '1.5rem', fontWeight: '600' }}>No Dataset Selected</h2>
          <p style={{ margin: 0, opacity: 0.7 }}>Select a dataset from the Dataset Manager to preview</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: isDarkMode ? '#0f0f0f' : '#f8fafc',
      color: isDarkMode ? '#e0e0e0' : '#1e293b',
      overflow: 'hidden',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        background: isDarkMode 
          ? 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)' 
          : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
        color: isDarkMode ? 'white' : '#1e293b',
        padding: '8px 20px',
        boxShadow: isDarkMode 
          ? '0 1px 3px rgba(0,0,0,0.3)' 
          : '0 1px 3px rgba(0,0,0,0.1)',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        position: 'relative'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600' }}>{dataset.name}</h1>
            <div style={{ display: 'flex', gap: '4px' }}>
              <span style={{
                background: isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(79, 70, 229, 0.1)',
                color: isDarkMode ? 'rgba(255,255,255,0.8)' : '#4f46e5',
                padding: '2px 6px',
                borderRadius: '6px',
                fontSize: '0.65rem',
                fontWeight: '500'
              }}>
                {dataset.format}
              </span>
              <span style={{
                background: isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(79, 70, 229, 0.1)',
                color: isDarkMode ? 'rgba(255,255,255,0.8)' : '#4f46e5',
                padding: '2px 6px',
                borderRadius: '6px',
                fontSize: '0.65rem',
                fontWeight: '500'
              }}>
                {dataset.sequence_length?.toLocaleString()} frames
              </span>
              {dataset.metadata?.has_ground_truth && (
                <span style={{
                  background: 'rgba(34, 197, 94, 0.1)',
                  color: '#22c55e',
                  padding: '2px 6px',
                  borderRadius: '6px',
                  fontSize: '0.65rem',
                  fontWeight: '500'
                }}>
                  GT
                </span>
              )}
            </div>
          </div>


          
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button 
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              style={{
                padding: '5px 7px',
                border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                background: isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.8)',
                borderRadius: '4px',
                cursor: 'pointer',
                color: isDarkMode ? '#e2e8f0' : '#64748b',
                fontSize: '0.75rem',
                transition: 'all 0.15s ease'
              }}
            >
              {sidebarCollapsed ? '→' : '←'}
            </button>
            
            <button 
              onClick={() => {
                const newTheme = !isDarkMode;
                setIsDarkMode(newTheme);
                localStorage.setItem('theme', newTheme ? 'dark' : 'light');
              }}
              style={{
                padding: '5px 7px',
                border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                background: isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.8)',
                borderRadius: '4px',
                cursor: 'pointer',
                color: isDarkMode ? '#e2e8f0' : '#64748b',
                fontSize: '0.75rem',
                transition: 'all 0.15s ease'
              }}
            >
              {isDarkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Visualization Area */}
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          background: isDarkMode ? '#1a1a1a' : 'white',
          margin: '6px',
          borderRadius: '8px',
          boxShadow: isDarkMode 
            ? '0 1px 3px rgba(0,0,0,0.3)' 
            : '0 1px 3px rgba(0,0,0,0.1)',
          overflow: 'hidden',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
        }}>
          {/* Title Bar */}
          <div style={{
            padding: '8px 16px',
            background: isDarkMode ? '#2d2d2d' : '#f8fafc',
            borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{
              fontSize: '0.9rem',
              fontWeight: '500',
              color: isDarkMode ? '#e2e8f0' : '#1e293b'
            }}>
              {viewMode === 'trajectory' && `Trajectory - Frame ${selectedFrame}`}
              {viewMode === 'lidar' && `Point Cloud - Frame ${selectedFrame} (${lidarData?.x?.length?.toLocaleString() || 0} pts)`}
              {viewMode === 'combined' && `SLAM View - Frame ${selectedFrame} (${lidarData?.x?.length?.toLocaleString() || 0} pts)`}
            </div>
            
            {/* View Mode Selector */}
            <div style={{
              display: 'flex',
              background: isDarkMode ? '#334155' : '#e2e8f0',
              borderRadius: '6px',
              padding: '2px'
            }}>
              <button 
                onClick={() => setViewMode('trajectory')}
                disabled={!dataset.metadata?.has_ground_truth}
                style={{
                  padding: '3px 8px',
                  border: 'none',
                  background: viewMode === 'trajectory' ? '#4f46e5' : 'transparent',
                  color: viewMode === 'trajectory' ? 'white' : (isDarkMode ? '#e2e8f0' : '#64748b'),
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.7rem',
                  fontWeight: '500',
                  opacity: !dataset.metadata?.has_ground_truth ? 0.4 : 1,
                  transition: 'all 0.15s ease'
                }}
              >
                📍 Trajectory
              </button>
              <button 
                onClick={() => setViewMode('lidar')}
                disabled={!dataset.sensors?.includes('velodyne')}
                style={{
                  padding: '3px 8px',
                  border: 'none',
                  background: viewMode === 'lidar' ? '#4f46e5' : 'transparent',
                  color: viewMode === 'lidar' ? 'white' : (isDarkMode ? '#e2e8f0' : '#64748b'),
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.7rem',
                  fontWeight: '500',
                  opacity: !dataset.sensors?.includes('velodyne') ? 0.4 : 1,
                  transition: 'all 0.15s ease'
                }}
              >
                ⚫ Point Cloud
              </button>
              <button 
                onClick={() => setViewMode('combined')}
                disabled={!dataset.metadata?.has_ground_truth || !dataset.sensors?.includes('velodyne')}
                style={{
                  padding: '3px 8px',
                  border: 'none',
                  background: viewMode === 'combined' ? '#4f46e5' : 'transparent',
                  color: viewMode === 'combined' ? 'white' : (isDarkMode ? '#e2e8f0' : '#64748b'),
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.7rem',
                  fontWeight: '500',
                  opacity: (!dataset.metadata?.has_ground_truth || !dataset.sensors?.includes('velodyne')) ? 0.4 : 1,
                  transition: 'all 0.15s ease'
                }}
              >
                🎯 SLAM View
              </button>
            </div>
          </div>

          {/* Plot Area with Controls */}
          <div style={{ flex: 1, position: 'relative' }}>
            {/* SolidWorks-style View Controls */}
            <div style={{
              position: 'absolute',
              top: '10px',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 1000,
              display: 'flex',
              gap: '3px',
              background: isDarkMode ? 'rgba(26, 26, 26, 0.95)' : 'rgba(255, 255, 255, 0.95)',
              borderRadius: '8px',
              padding: '4px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              boxShadow: isDarkMode 
                ? '0 2px 8px rgba(0,0,0,0.3)' 
                : '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              <button
                onClick={() => {
                  const plotDiv = document.querySelector('.js-plotly-plot');
                  if (plotDiv && window.Plotly) {
                    window.Plotly.relayout(plotDiv, {
                      'scene.camera': {
                        eye: { x: 0, y: 0, z: 2.5 },
                        center: { x: 0, y: 0, z: 0 }
                      }
                    });
                  }
                }}
                style={{
                  width: '26px',
                  height: '26px',
                  border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                  background: isDarkMode ? '#334155' : 'white',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  color: isDarkMode ? '#e2e8f0' : '#64748b',
                  transition: 'all 0.15s ease'
                }}
                title="Top View"
              >
                📷
              </button>
              <button
                onClick={() => {
                  const plotDiv = document.querySelector('.js-plotly-plot');
                  if (plotDiv && window.Plotly) {
                    window.Plotly.relayout(plotDiv, {
                      'scene.camera': {
                        eye: { x: 2.5, y: 0, z: 0 },
                        center: { x: 0, y: 0, z: 0 }
                      }
                    });
                  }
                }}
                style={{
                  width: '26px',
                  height: '26px',
                  border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                  background: isDarkMode ? '#334155' : 'white',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  color: isDarkMode ? '#e2e8f0' : '#64748b',
                  transition: 'all 0.15s ease'
                }}
                title="Front View"
              >
                🔍
              </button>
              <button
                onClick={() => {
                  const plotDiv = document.querySelector('.js-plotly-plot');
                  if (plotDiv && window.Plotly) {
                    window.Plotly.relayout(plotDiv, {
                      'scene.camera': {
                        eye: { x: 1.5, y: 1.5, z: 1.5 },
                        center: { x: 0, y: 0, z: 0 }
                      }
                    });
                  }
                }}
                style={{
                  width: '26px',
                  height: '26px',
                  border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                  background: isDarkMode ? '#334155' : 'white',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  color: isDarkMode ? '#e2e8f0' : '#64748b',
                  transition: 'all 0.15s ease'
                }}
                title="Isometric View"
              >
                🏠
              </button>
              <div style={{ 
                width: '1px', 
                height: '20px', 
                background: isDarkMode ? '#475569' : '#d1d5db',
                margin: '3px 2px'
              }} />
              <button
                onClick={() => {
                  const plotDiv = document.querySelector('.js-plotly-plot');
                  if (plotDiv && window.Plotly) {
                    window.Plotly.relayout(plotDiv, 'scene.camera', null);
                  }
                }}
                style={{
                  width: '26px',
                  height: '26px',
                  border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                  background: isDarkMode ? '#334155' : 'white',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  color: isDarkMode ? '#e2e8f0' : '#64748b',
                  transition: 'all 0.15s ease'
                }}
                title="Zoom to Fit"
              >
                ⊞
              </button>
              <button
                style={{
                  width: '26px',
                  height: '26px',
                  border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                  background: isDarkMode ? '#334155' : 'white',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  color: isDarkMode ? '#e2e8f0' : '#64748b',
                  transition: 'all 0.15s ease'
                }}
                title="Pan"
              >
                ✋
              </button>
              <button
                style={{
                  width: '26px',
                  height: '26px',
                  border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                  background: isDarkMode ? '#334155' : 'white',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  color: isDarkMode ? '#e2e8f0' : '#64748b',
                  transition: 'all 0.15s ease'
                }}
                title="Rotate"
              >
                ↻
              </button>
            </div>

            {viewMode === 'trajectory' && renderTrajectoryPlot()}
            {viewMode === 'lidar' && renderLidarPlot()}
            {viewMode === 'combined' && renderCombinedView()}
          </div>
        </div>

        {/* Sidebar */}
        {!sidebarCollapsed && (
          <div style={{ 
            width: '320px', 
            display: 'flex', 
            flexDirection: 'column',
            gap: '6px',
            margin: '6px 6px 6px 0'
          }}>
            {/* Frame Controls */}
            <div style={{
              background: isDarkMode ? '#1a1a1a' : 'white',
              borderRadius: '8px',
              padding: '16px',
              boxShadow: isDarkMode 
                ? '0 1px 3px rgba(0,0,0,0.3)' 
                : '0 1px 3px rgba(0,0,0,0.1)',
              border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
            }}>
              <h4 style={{ 
                margin: '0 0 12px 0', 
                color: isDarkMode ? '#e0e0e0' : '#1e293b',
                fontSize: '0.9rem',
                fontWeight: '600'
              }}>
                Frame Navigation
              </h4>
              
              <div style={{ marginBottom: '12px' }}>
                <input 
                  type="range" 
                  min="0" 
                  max={dataset.sequence_length - 1}
                  value={selectedFrame}
                  onChange={(e) => {
                    const newFrame = parseInt(e.target.value);
                    setSelectedFrame(newFrame);
                    setIsPlaying(false);
                  }}
                  style={{
                    width: '100%',
                    height: '4px',
                    borderRadius: '2px',
                    background: isDarkMode ? '#334155' : '#e2e8f0',
                    outline: 'none',
                    marginBottom: '8px',
                    cursor: 'pointer'
                  }}
                />
                <div style={{
                  textAlign: 'center',
                  fontFamily: 'monospace',
                  color: isDarkMode ? '#94a3b8' : '#64748b',
                  fontSize: '0.8rem',
                  background: isDarkMode ? '#334155' : '#f1f5f9',
                  padding: '6px',
                  borderRadius: '4px'
                }}>
                  Frame <strong style={{ color: isDarkMode ? '#00d4ff' : '#4f46e5' }}>{selectedFrame}</strong> / {dataset.sequence_length - 1}
                </div>
              </div>

              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '12px'
              }}>
                <div style={{ display: 'flex', gap: '4px' }}>
                  <button 
                    onClick={() => setSelectedFrame(0)}
                    style={{
                      padding: '6px 8px',
                      border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                      background: isDarkMode ? '#334155' : 'white',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      color: isDarkMode ? '#e0e0e0' : '#374151',
                      fontSize: '0.75rem'
                    }}
                  >
                    ⏮️
                  </button>
                  <button 
                    onClick={() => setSelectedFrame(Math.max(0, selectedFrame - 1))}
                    style={{
                      padding: '6px 8px',
                      border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                      background: isDarkMode ? '#334155' : 'white',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      color: isDarkMode ? '#e0e0e0' : '#374151',
                      fontSize: '0.75rem'
                    }}
                  >
                    ⏪
                  </button>
                  <button 
                    onClick={() => setIsPlaying(!isPlaying)}
                    style={{
                      padding: '6px 8px',
                      border: `1px solid ${isDarkMode ? '#00d4ff' : '#4f46e5'}`,
                      background: isPlaying ? (isDarkMode ? '#00d4ff' : '#4f46e5') : (isDarkMode ? '#334155' : 'white'),
                      borderRadius: '4px',
                      cursor: 'pointer',
                      color: isPlaying ? 'white' : (isDarkMode ? '#e0e0e0' : '#374151'),
                      fontSize: '0.75rem'
                    }}
                  >
                    {isPlaying ? '⏸️' : '▶️'}
                  </button>
                  <button 
                    onClick={() => setSelectedFrame(Math.min(dataset.sequence_length - 1, selectedFrame + 1))}
                    style={{
                      padding: '6px 8px',
                      border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                      background: isDarkMode ? '#334155' : 'white',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      color: isDarkMode ? '#e0e0e0' : '#374151',
                      fontSize: '0.75rem'
                    }}
                  >
                    ⏩
                  </button>
                  <button 
                    onClick={() => setSelectedFrame(dataset.sequence_length - 1)}
                    style={{
                      padding: '6px 8px',
                      border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                      background: isDarkMode ? '#334155' : 'white',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      color: isDarkMode ? '#e0e0e0' : '#374151',
                      fontSize: '0.75rem'
                    }}
                  >
                    ⏭️
                  </button>
                </div>
                
                <select 
                  value={playSpeed}
                  onChange={(e) => setPlaySpeed(parseInt(e.target.value))}
                  style={{
                    padding: '4px 6px',
                    border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                    borderRadius: '4px',
                    background: isDarkMode ? '#334155' : 'white',
                    color: isDarkMode ? '#e0e0e0' : '#374151',
                    fontSize: '0.75rem'
                  }}
                >
                  <option value={500}>0.5x</option>
                  <option value={200}>1x</option>
                  <option value={100}>2x</option>
                  <option value={50}>4x</option>
                  <option value={25}>8x</option>
                </select>
              </div>

              {(viewMode === 'lidar' || viewMode === 'combined') && (
                <div>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '6px', 
                    fontSize: '0.8rem', 
                    color: isDarkMode ? '#94a3b8' : '#64748b',
                    fontWeight: '500'
                  }}>
                    Point Cloud Quality:
                  </label>
                  <select 
                    value={lidarResolution}
                    onChange={(e) => setLidarResolution(parseInt(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '6px 8px',
                      border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                      borderRadius: '4px',
                      background: isDarkMode ? '#334155' : 'white',
                      color: isDarkMode ? '#e0e0e0' : '#374151',
                      fontSize: '0.8rem'
                    }}
                  >
                    <option value={5000}>5K points (Fast)</option>
                    <option value={10000}>10K points (Balanced)</option>
                    <option value={20000}>20K points (High)</option>
                    <option value={50000}>50K points (Ultra)</option>
                    <option value={100000}>100K+ points (Maximum)</option>
                  </select>
                </div>
              )}
            </div>

            {/* Camera Views */}
            <div style={{
              flex: 1,
              background: isDarkMode ? '#1a1a1a' : 'white',
              borderRadius: '8px',
              padding: '16px',
              boxShadow: isDarkMode 
                ? '0 1px 3px rgba(0,0,0,0.3)' 
                : '0 1px 3px rgba(0,0,0,0.1)',
              overflow: 'auto',
              border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
            }}>
              <h4 style={{ 
                margin: '0 0 12px 0', 
                color: isDarkMode ? '#e0e0e0' : '#1e293b',
                fontSize: '0.9rem',
                fontWeight: '600'
              }}>
                Camera Views
              </h4>
              
              <div style={{ display: 'grid', gap: '8px' }}>
                {dataset.sensors?.filter(s => s.startsWith('image')).map(sensor => (
                  <div key={sensor} style={{
                    border: `1px solid ${isDarkMode ? '#475569' : '#e2e8f0'}`,
                    borderRadius: '6px',
                    overflow: 'hidden',
                    background: isDarkMode ? '#334155' : '#f8fafc'
                  }}>
                    <div style={{
                      padding: '6px 8px',
                      background: isDarkMode ? '#475569' : '#f1f5f9',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <span style={{ 
                        fontWeight: '500', 
                        fontSize: '0.75rem',
                        color: isDarkMode ? '#e0e0e0' : '#1e293b'
                      }}>
                        {sensor.replace('_', ' ').toUpperCase()}
                      </span>
                      <span style={{
                        fontSize: '0.65rem',
                        color: isDarkMode ? '#94a3b8' : '#64748b',
                        background: isDarkMode ? '#64748b' : '#e2e8f0',
                        padding: '1px 4px',
                        borderRadius: '3px'
                      }}>
                        {sensor.includes('0') || sensor.includes('1') ? 'Mono' : 'Color'}
                      </span>
                    </div>
                    <div style={{ 
                      minHeight: '80px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <img 
                        src={`/api/datasets/${dataset.id}/frame/${selectedFrame}/${sensor}`}
                        alt={`${sensor} frame ${selectedFrame}`}
                        style={{ 
                          width: '100%', 
                          height: 'auto', 
                          maxHeight: '100px',
                          objectFit: 'cover'
                        }}
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.parentElement.innerHTML = `<div style="color: ${isDarkMode ? '#94a3b8' : '#64748b'}; font-size: 0.7rem;">Image not available</div>`;
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {groundTruth && (
                <div style={{
                  marginTop: '12px',
                  padding: '12px',
                  background: isDarkMode ? '#334155' : '#f8fafc',
                  borderRadius: '6px',
                  border: `1px solid ${isDarkMode ? '#475569' : '#e2e8f0'}`
                }}>
                  <h5 style={{ 
                    margin: '0 0 8px 0', 
                    color: isDarkMode ? '#e0e0e0' : '#1e293b',
                    fontSize: '0.8rem',
                    fontWeight: '600'
                  }}>
                    Frame Details
                  </h5>
                  <div style={{ fontSize: '0.75rem', lineHeight: '1.4' }}>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      marginBottom: '4px'
                    }}>
                      <span style={{ color: isDarkMode ? '#94a3b8' : '#64748b' }}>Frame ID:</span>
                      <span style={{ color: isDarkMode ? '#e0e0e0' : '#1e293b', fontWeight: '500' }}>
                        {selectedFrame}
                      </span>
                    </div>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      marginBottom: '4px'
                    }}>
                      <span style={{ color: isDarkMode ? '#94a3b8' : '#64748b' }}>Position:</span>
                      <span style={{ 
                        color: isDarkMode ? '#e0e0e0' : '#1e293b', 
                        fontWeight: '500',
                        fontFamily: 'monospace',
                        fontSize: '0.7rem'
                      }}>
                        {groundTruth[selectedFrame]?.position.map(p => p.toFixed(2)).join(', ')} m
                      </span>
                    </div>
                    <div style={{ marginTop: '8px' }}>
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '3px'
                      }}>
                        <span style={{ color: isDarkMode ? '#94a3b8' : '#64748b' }}>Progress:</span>
                        <span style={{ 
                          color: isDarkMode ? '#00d4ff' : '#4f46e5', 
                          fontWeight: '600',
                          fontSize: '0.7rem'
                        }}>
                          {((selectedFrame / (dataset.sequence_length - 1)) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div style={{
                        height: '3px',
                        background: isDarkMode ? '#475569' : '#e2e8f0',
                        borderRadius: '2px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          height: '100%',
                          background: isDarkMode 
                            ? 'linear-gradient(90deg, #00d4ff 0%, #0ea5e9 100%)' 
                            : 'linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%)',
                          borderRadius: '2px',
                          width: `${(selectedFrame / (dataset.sequence_length - 1)) * 100}%`,
                          transition: 'width 0.2s ease'
                        }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DatasetPreview;