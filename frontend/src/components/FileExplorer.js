import React, { useState } from 'react';

const FileExplorer = ({ files = {}, activeFile, onFileSelect, onNewFile, isDarkMode }) => {
  const [expandedFolders, setExpandedFolders] = useState(new Set(['algorithm', 'tests']));
  const [newFileName, setNewFileName] = useState('');
  const [showNewFileInput, setShowNewFileInput] = useState(false);

  const toggleFolder = (folderPath) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderPath)) {
      newExpanded.delete(folderPath);
    } else {
      newExpanded.add(folderPath);
    }
    setExpandedFolders(newExpanded);
  };

  const createNewFile = () => {
    if (newFileName.trim()) {
      onNewFile(newFileName.trim());
      setNewFileName('');
      setShowNewFileInput(false);
    }
  };

  const organizeFiles = () => {
    const organized = {};
    
    Object.keys(files).forEach(filepath => {
      const parts = filepath.split('/');
      let current = organized;
      
      parts.forEach((part, index) => {
        if (index === parts.length - 1) {
          // This is a file
          current[part] = { type: 'file', path: filepath };
        } else {
          // This is a folder
          if (!current[part]) {
            current[part] = { type: 'folder', children: {} };
          }
          current = current[part].children;
        }
      });
    });
    
    return organized;
  };

  const renderFileTree = (items, basePath = '') => {
    return Object.entries(items).map(([name, item]) => {
      const fullPath = basePath ? `${basePath}/${name}` : name;
      
      if (item.type === 'folder') {
        const isExpanded = expandedFolders.has(fullPath);
        
        return (
          <div key={fullPath}>
            <div
              onClick={() => toggleFolder(fullPath)}
              style={{
                padding: '4px 8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.8rem',
                color: isDarkMode ? '#e2e8f0' : '#1e293b',
                background: 'transparent'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = isDarkMode ? '#334155' : '#f1f5f9';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
              }}
            >
              <span style={{ fontSize: '0.7rem' }}>
                {isExpanded ? '📂' : '📁'}
              </span>
              <span>{name}</span>
            </div>
            {isExpanded && (
              <div style={{ marginLeft: '16px' }}>
                {renderFileTree(item.children, fullPath)}
              </div>
            )}
          </div>
        );
      } else {
        const isActive = activeFile === item.path;
        
        return (
          <div
            key={item.path}
            onClick={() => onFileSelect(item.path)}
            style={{
              padding: '4px 8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.8rem',
              color: isActive 
                ? (isDarkMode ? '#4ade80' : '#16a34a')
                : (isDarkMode ? '#e2e8f0' : '#1e293b'),
              background: isActive 
                ? (isDarkMode ? 'rgba(74, 222, 128, 0.1)' : 'rgba(22, 163, 74, 0.1)')
                : 'transparent',
              borderRadius: '4px',
              margin: '1px 0'
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = isDarkMode ? '#334155' : '#f1f5f9';
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = 'transparent';
              }
            }}
          >
            <span style={{ fontSize: '0.7rem' }}>
              {getFileIcon(name)}
            </span>
            <span>{name}</span>
          </div>
        );
      }
    });
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    const iconMap = {
      'py': '🐍',
      'js': '📜',
      'ts': '📘',
      'cpp': '⚙️',
      'c': '⚙️',
      'h': '📋',
      'hpp': '📋',
      'java': '☕',
      'json': '📄',
      'yaml': '📄',
      'yml': '📄',
      'xml': '📄',
      'html': '🌐',
      'css': '🎨',
      'md': '📝',
      'txt': '📄'
    };
    return iconMap[ext] || '📄';
  };

  const organizedFiles = organizeFiles();

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: isDarkMode ? '#1a1a1a' : 'white'
    }}>
      {/* Explorer Header */}
      <div style={{
        padding: '8px 12px',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <span style={{
          fontSize: '0.8rem',
          fontWeight: '600',
          color: isDarkMode ? '#e2e8f0' : '#1e293b'
        }}>
          📁 Explorer
        </span>
        <button
          onClick={() => setShowNewFileInput(true)}
          style={{
            background: 'none',
            border: 'none',
            color: isDarkMode ? '#94a3b8' : '#64748b',
            cursor: 'pointer',
            fontSize: '0.8rem',
            padding: '2px'
          }}
          title="New File"
        >
          ➕
        </button>
      </div>

      {/* New File Input */}
      {showNewFileInput && (
        <div style={{
          padding: '8px 12px',
          borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          background: isDarkMode ? '#2d2d2d' : '#f8fafc'
        }}>
          <input
            type="text"
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                createNewFile();
              } else if (e.key === 'Escape') {
                setShowNewFileInput(false);
                setNewFileName('');
              }
            }}
            placeholder="filename.py"
            autoFocus
            style={{
              width: '100%',
              padding: '4px 8px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '4px',
              background: isDarkMode ? '#334155' : 'white',
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              fontSize: '0.8rem'
            }}
          />
          <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
            <button
              onClick={createNewFile}
              style={{
                padding: '2px 6px',
                background: '#4f46e5',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                fontSize: '0.7rem',
                cursor: 'pointer'
              }}
            >
              Create
            </button>
            <button
              onClick={() => {
                setShowNewFileInput(false);
                setNewFileName('');
              }}
              style={{
                padding: '2px 6px',
                background: 'transparent',
                color: isDarkMode ? '#94a3b8' : '#64748b',
                border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                borderRadius: '3px',
                fontSize: '0.7rem',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* File Tree */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '8px 4px'
      }}>
        {Object.keys(organizedFiles).length > 0 ? (
          renderFileTree(organizedFiles)
        ) : (
          <div style={{
            padding: '20px',
            textAlign: 'center',
            color: isDarkMode ? '#94a3b8' : '#64748b',
            fontSize: '0.8rem'
          }}>
            <div style={{ fontSize: '2rem', marginBottom: '8px', opacity: 0.3 }}>📁</div>
            <p style={{ margin: 0 }}>No files yet</p>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.7rem' }}>
              Click + to create a new file
            </p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div style={{
        padding: '8px 12px',
        borderTop: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        background: isDarkMode ? '#2d2d2d' : '#f8fafc'
      }}>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => onNewFile('algorithm/new_algorithm.py')}
            style={{
              flex: 1,
              padding: '4px 6px',
              background: 'transparent',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '4px',
              color: isDarkMode ? '#e2e8f0' : '#64748b',
              fontSize: '0.7rem',
              cursor: 'pointer'
            }}
          >
            🐍 New Python
          </button>
          <button
            onClick={() => onNewFile('tests/test_new.py')}
            style={{
              flex: 1,
              padding: '4px 6px',
              background: 'transparent',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '4px',
              color: isDarkMode ? '#e2e8f0' : '#64748b',
              fontSize: '0.7rem',
              cursor: 'pointer'
            }}
          >
            🧪 New Test
          </button>
        </div>
      </div>
    </div>
  );
};

export default FileExplorer;