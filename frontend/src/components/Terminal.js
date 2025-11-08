import React, { useEffect, useRef, useState } from 'react';

const Terminal = ({ isDarkMode, onCommand }) => {
  const [history, setHistory] = useState([]);
  const [currentCommand, setCurrentCommand] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const terminalRef = useRef(null);
  const inputRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      wsRef.current = new WebSocket('ws://localhost:8007/ws/terminal');
      
      wsRef.current.onopen = () => {
        setIsConnected(true);
        addToHistory('🟢 Terminal connected', 'system');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'output') {
            // Handle raw terminal output (preserve formatting)
            const content = data.content;
            if (content) {
              // Split by lines but preserve empty lines for formatting
              const lines = content.split('\n');
              lines.forEach((line, index) => {
                // Don't skip empty lines as they may be important for formatting
                addToHistory(line, 'output');
              });
            }
          } else if (data.type === 'error') {
            addToHistory(data.content, 'error');
          } else if (data.type === 'system') {
            addToHistory(data.content, 'system');
          }
        } catch (error) {
          // Fallback for non-JSON messages
          addToHistory(event.data, 'output');
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        addToHistory('🔴 Terminal session disconnected', 'system');
      };

      wsRef.current.onerror = () => {
        setIsConnected(false);
        addToHistory('⚠️ Terminal connection error', 'system');
      };
    } catch (error) {
      setIsConnected(false);
      addToHistory('⚠️ WebSocket connection failed', 'system');
    }
  };

  const addToHistory = (content, type = 'output') => {
    setHistory(prev => [...prev, {
      id: Date.now(),
      content,
      type,
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  const executeCommand = () => {
    if (!currentCommand.trim()) return;

    addToHistory(`$ ${currentCommand}`, 'command');

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({
          type: 'command',
          command: currentCommand
        }));
      } catch (error) {
        addToHistory('❌ Failed to send command to terminal', 'error');
      }
    } else {
      addToHistory('❌ Terminal not connected', 'error');
    }

    if (onCommand) {
      onCommand(currentCommand);
    }

    setCurrentCommand('');
  };



  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      executeCommand();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      // TODO: Implement command history navigation
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      // TODO: Implement command history navigation
    }
  };

  const scrollToBottom = () => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: isDarkMode ? '#1a1a1a' : '#ffffff',
      border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      {/* Terminal Header */}
      <div style={{
        padding: '8px 16px',
        background: isDarkMode ? '#2d2d2d' : '#f8fafc',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: isConnected ? '#22c55e' : '#ef4444'
          }} />
          <span style={{
            fontSize: '0.8rem',
            color: isDarkMode ? '#e2e8f0' : '#1e293b',
            fontWeight: '500'
          }}>
            Terminal
          </span>
        </div>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => setHistory([])}
            style={{
              padding: '4px 8px',
              background: 'transparent',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '4px',
              color: isDarkMode ? '#e2e8f0' : '#64748b',
              fontSize: '0.7rem',
              cursor: 'pointer'
            }}
          >
            Clear
          </button>
          <button
            onClick={connectWebSocket}
            disabled={isConnected}
            style={{
              padding: '4px 8px',
              background: 'transparent',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '4px',
              color: isDarkMode ? '#e2e8f0' : '#64748b',
              fontSize: '0.7rem',
              cursor: isConnected ? 'not-allowed' : 'pointer',
              opacity: isConnected ? 0.5 : 1
            }}
          >
            Reconnect
          </button>
        </div>
      </div>

      {/* Terminal Output */}
      <div
        ref={terminalRef}
        style={{
          flex: 1,
          padding: '12px',
          overflow: 'auto',
          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
          fontSize: '0.8rem',
          lineHeight: '1.4'
        }}
      >
        {history.map(entry => (
          <div
            key={entry.id}
            style={{
              marginBottom: '2px',
              color: entry.type === 'command' 
                ? (isDarkMode ? '#4ade80' : '#16a34a')
                : entry.type === 'error'
                ? (isDarkMode ? '#f87171' : '#dc2626')
                : entry.type === 'system'
                ? (isDarkMode ? '#60a5fa' : '#2563eb')
                : (isDarkMode ? '#e2e8f0' : '#1e293b')
            }}
          >
            {entry.content}
          </div>
        ))}
      </div>

      {/* Terminal Input */}
      <div style={{
        padding: '8px 12px',
        borderTop: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <span style={{
          color: isDarkMode ? '#4ade80' : '#16a34a',
          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
          fontSize: '0.8rem'
        }}>
          $
        </span>
        <input
          ref={inputRef}
          type="text"
          value={currentCommand}
          onChange={(e) => setCurrentCommand(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Enter command..."
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: isDarkMode ? '#e2e8f0' : '#1e293b',
            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
            fontSize: '0.8rem'
          }}
        />
        <button
          onClick={executeCommand}
          disabled={!currentCommand.trim()}
          style={{
            padding: '4px 8px',
            background: currentCommand.trim() ? '#4f46e5' : 'transparent',
            border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
            borderRadius: '4px',
            color: currentCommand.trim() ? 'white' : (isDarkMode ? '#94a3b8' : '#64748b'),
            fontSize: '0.7rem',
            cursor: currentCommand.trim() ? 'pointer' : 'not-allowed'
          }}
        >
          Run
        </button>
      </div>
    </div>
  );
};

export default Terminal;