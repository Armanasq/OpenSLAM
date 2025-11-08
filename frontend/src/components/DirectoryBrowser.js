import React, { useState, useEffect } from 'react';

const DirectoryBrowser = ({ isOpen, onClose, onSelect, isDarkMode, initialPath = '/home' }) => {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [directories, setDirectories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadDirectories(currentPath);
    }
  }, [isOpen, currentPath]);

  const loadDirectories = async (path) => {
    setLoading(true);
    setError('');
    
    try {
      // Mock directory listing - in real implementation, this would call your backend
      const mockDirectories = [
        { name: '..', isDirectory: true, path: getParentPath(path) },
        { name: 'data', isDirectory: true, path: `${path}/data` },
        { name: 'datasets', isDirectory: true, path: `${path}/datasets` },
        { name: 'KITTI', isDirectory: true, path: `${path}/KITTI` },
        { name: '00', isDirectory: true, path: `${path}/00` },
        { name: '01', isDirectory: true, path: `${path}/01` },
        { name: 'Documents', isDirectory: true, path: `${path}/Documents` },
        { name: 'Downloads', isDirectory: true, path: `${path}/Downloads` }
      ];
      
      // Filter out parent directory if we're at root
      const filteredDirs = path === '/' 
        ? mockDirectories.filter(dir => dir.name !== '..')
        : mockDirectories;
      
      setDirectories(filteredDirs);
    } catch (err) {
      setError('Failed to load directories');
    } finally {
      setLoading(false);
    }
  };

  const getParentPath = (path) => {
    if (path === '/') return '/';
    const parts = path.split('/').filter(Boolean);
    parts.pop();
    return parts.length === 0 ? '/' : '/' + parts.join('/');
  };

  const handleDirectoryClick = (directory) => {
    if (directory.name === '..') {
      setCurrentPath(directory.path);
    } else if (directory.isDirectory) {
      setCurrentPath(directory.path);
    }
  };

  const handleSelect = () => {
    onSelect(currentPath);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000
    }}>
      <div style={{
        width: '600px',
        maxWidth: '90vw',
        height: '500px',
        background: isDarkMode ? '#1a1a1a' : 'white',
        borderRadius: '12px',
        border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <h3 style={{
            margin: 0,
            fontSize: '1.25rem',
            fontWeight: '600',
            color: isDarkMode ? '#e2e8f0' : '#1e293b'
          }}>
            Select Dataset Directory
          </h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: isDarkMode ? '#94a3b8' : '#64748b',
              cursor: 'pointer',
              fontSize: '24px',
              padding: '4px'
            }}
          >
            ✕
          </button>
        </div>

        {/* Current Path */}
        <div style={{
          padding: '16px 20px',
          background: isDarkMode ? '#334155' : '#f8fafc',
          borderBottom: `1px solid ${isDarkMode ? '#475569' : '#e2e8f0'}`,
          display: 'flex',
          alignItems: 'center'
        }}>
          <span style={{
            fontSize: '0.9rem',
            color: isDarkMode ? '#94a3b8' : '#64748b',
            marginRight: '8px'
          }}>
            📁
          </span>
          <span style={{
            fontSize: '0.9rem',
            color: isDarkMode ? '#e2e8f0' : '#1e293b',
            fontFamily: 'monospace'
          }}>
            {currentPath}
          </span>
        </div>

        {/* Directory List */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '8px'
        }}>
          {loading ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '200px',
              color: isDarkMode ? '#94a3b8' : '#64748b'
            }}>
              Loading directories...
            </div>
          ) : error ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '200px',
              color: '#ef4444'
            }}>
              {error}
            </div>
          ) : (
            <div>
              {directories.map((directory, index) => (
                <div
                  key={index}
                  onClick={() => handleDirectoryClick(directory)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '12px 16px',
                    cursor: 'pointer',
                    borderRadius: '6px',
                    margin: '2px 0',
                    transition: 'background 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = isDarkMode ? '#334155' : '#f1f5f9';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <span style={{
                    fontSize: '18px',
                    marginRight: '12px'
                  }}>
                    {directory.name === '..' ? '↩️' : '📁'}
                  </span>
                  <span style={{
                    fontSize: '0.9rem',
                    color: isDarkMode ? '#e2e8f0' : '#1e293b',
                    fontWeight: directory.name === '..' ? '500' : '400'
                  }}>
                    {directory.name === '..' ? 'Parent Directory' : directory.name}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '20px',
          borderTop: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{
            fontSize: '0.8rem',
            color: isDarkMode ? '#94a3b8' : '#64748b'
          }}>
            Select a directory containing KITTI dataset
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={onClose}
              style={{
                padding: '8px 16px',
                border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                background: 'transparent',
                color: isDarkMode ? '#e2e8f0' : '#64748b',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSelect}
              style={{
                padding: '8px 16px',
                border: 'none',
                background: '#4f46e5',
                color: 'white',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: '500'
              }}
            >
              Select Directory
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DirectoryBrowser;