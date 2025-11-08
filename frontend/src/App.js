import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navigation from './components/Navigation';
import LandingPage from './components/LandingPage';
import DatasetManager from './components/DatasetManager';
import DatasetPreview from './components/DatasetPreview';
import AlgorithmDevelopment from './components/AlgorithmDevelopment';
import Visualization from './components/Visualization';
import TutorialInterface from './components/TutorialInterface';
import PerformanceAnalysis from './components/PerformanceAnalysis';
import './App.css';

const App = () => {
  const [currentDataset, setCurrentDataset] = useState(null);
  const [algorithms, setAlgorithms] = useState([]);
  const [executionResults, setExecutionResults] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    initializeWebSocket();
    loadInitialData();
    
    // Load theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const initializeWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8007/ws');
    
    ws.onopen = () => {
      setIsConnected(true);
      addNotification('Connected to SLAM backend', 'success');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      addNotification('Disconnected from backend', 'error');
    };
    
    ws.onerror = (error) => {
      addNotification('WebSocket error occurred', 'error');
    };
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'algorithm_result':
        setExecutionResults(prev => [...prev, data.payload]);
        addNotification(`Algorithm ${data.payload.algorithm_name} completed`, 'success');
        break;
      case 'dataset_loaded':
        setCurrentDataset(data.payload);
        addNotification(`Dataset ${data.payload.name} loaded`, 'info');
        break;
      case 'error':
        addNotification(data.message, 'error');
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const loadInitialData = async () => {
    try {
      const response = await fetch('/api/datasets');
      if (response.ok) {
        const datasets = await response.json();
        if (datasets.length > 0) {
          setCurrentDataset(datasets[0]);
        }
      }
    } catch (error) {
      addNotification('Failed to load initial data', 'error');
    }
  };

  const addNotification = (message, type = 'info') => {
    const notification = {
      id: Date.now(),
      message,
      type,
      timestamp: new Date()
    };
    setNotifications(prev => [...prev, notification]);
    
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  const handleDatasetSelect = (dataset) => {
    setCurrentDataset(dataset);
    addNotification(`Selected dataset: ${dataset.name}`, 'info');
  };

  const handleAlgorithmCreate = (algorithm) => {
    setAlgorithms(prev => [...prev, algorithm]);
    addNotification(`Algorithm ${algorithm.name} created`, 'success');
  };

  const handleAlgorithmExecute = async (algorithmId, datasetId, parameters) => {
    try {
      const response = await fetch('/api/execute-algorithm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          algorithm_id: algorithmId,
          dataset_id: datasetId,
          parameters
        })
      });
      
      if (response.ok) {
        addNotification('Algorithm execution started', 'info');
      } else {
        addNotification('Failed to start algorithm execution', 'error');
      }
    } catch (error) {
      addNotification('Error executing algorithm', 'error');
    }
  };

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <Router>
      <div className={`app ${isDarkMode ? 'dark' : ''}`}>
        <Navigation 
          isConnected={isConnected}
          currentDataset={currentDataset}
          onDatasetSelect={handleDatasetSelect}
          isDarkMode={isDarkMode}
          onToggleTheme={toggleTheme}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
        
        <main className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
          <Routes>
            <Route 
              path="/" 
              element={<LandingPage isDarkMode={isDarkMode} />} 
            />
            <Route 
              path="/datasets" 
              element={
                <DatasetManager 
                  currentDataset={currentDataset}
                  onDatasetSelect={handleDatasetSelect}
                  onNotification={addNotification}
                  isDarkMode={isDarkMode}
                />
              } 
            />
            <Route 
              path="/dataset-preview" 
              element={
                <DatasetPreview 
                  dataset={currentDataset}
                  onNotification={addNotification}
                  isDarkMode={isDarkMode}
                />
              } 
            />
            <Route 
              path="/algorithms" 
              element={
                <AlgorithmDevelopment 
                  algorithms={algorithms}
                  currentDataset={currentDataset}
                  onAlgorithmCreate={handleAlgorithmCreate}
                  onAlgorithmExecute={handleAlgorithmExecute}
                  onNotification={addNotification}
                  isDarkMode={isDarkMode}
                />
              } 
            />
            <Route 
              path="/visualization" 
              element={
                <Visualization 
                  executionResults={executionResults}
                  currentDataset={currentDataset}
                  onNotification={addNotification}
                  isDarkMode={isDarkMode}
                />
              } 
            />
            <Route 
              path="/tutorials" 
              element={
                <TutorialInterface 
                  onNotification={addNotification}
                  isDarkMode={isDarkMode}
                />
              } 
            />
            <Route 
              path="/analysis" 
              element={
                <PerformanceAnalysis 
                  executionResults={executionResults}
                  onNotification={addNotification}
                  isDarkMode={isDarkMode}
                />
              } 
            />
          </Routes>
        </main>
        
        <NotificationContainer notifications={notifications} isDarkMode={isDarkMode} />
      </div>
    </Router>
  );
};

const NotificationContainer = ({ notifications, isDarkMode }) => {
  if (notifications.length === 0) return null;

  return (
    <div className="notification-container">
      {notifications.map(notification => (
        <div 
          key={notification.id} 
          className={`notification notification-${notification.type} ${isDarkMode ? 'dark' : ''}`}
        >
          <div className="notification-content">
            <div className="flex items-start gap-3">
              <div className="notification-icon">
                {notification.type === 'success' && '✓'}
                {notification.type === 'error' && '✕'}
                {notification.type === 'warning' && '⚠'}
                {notification.type === 'info' && 'ℹ'}
              </div>
              <div className="flex-1">
                <div className="notification-message">{notification.message}</div>
                <div className="notification-time">
                  {notification.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default App;