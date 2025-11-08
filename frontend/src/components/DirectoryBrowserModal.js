import React, { useState, useEffect } from 'react';

const DirectoryBrowserModal = ({ isOpen, onClose, onSelectDirectory, isDarkMode }) => {
  const [currentPath, setCurrentPath] = useState('/');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      browseDirectory(currentPath);
    }
  }, [isOpen, currentPath]);

  const browseDirectory = async (path) => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/browse-directory', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ path })
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentPath(data.current_path);
        setItems(data.items);
        console.log('Directory data:', data); // Debug log
      } else {
        const errorData = await response.json();
        setError(`Error: ${errorData.detail || 'Failed to browse directory'}`);
      }
    } catch (error) {
      console.error('Error browsing directory:', error);
      setError(`Network error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = (item) => {
    if (item.type === 'directory') {
      setCurrentPath(item.path);
    }
  };

  const handleSelectCurrent = () => {
    onSelectDirectory(currentPath);
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
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: isDarkMode ? '#1e293b' : 'white',
        borderRadius: '12px',
        width: '600px',
        maxHeight: '500px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: `1px solid ${isDarkMode ? '#374151' : '#e5e7eb'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h3 style={{
            margin: 0,
            color: isDarkMode ? '#f1f5f9' : '#1f2937',
            fontSize: '1.2rem'
          }}>
            Select Directory
          </h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: isDarkMode ? '#9ca3af' : '#6b7280',
              padding: '4px'
            }}
          >
            ×
          </button>
        </div>

        {/* Current Path */}
        <div style={{
          padding: '16px 20px',
          backgroundColor: isDarkMode ? '#374151' : '#f9fafb',
          borderBottom: `1px solid ${isDarkMode ? '#4b5563' : '#e5e7eb'}`
        }}>
          <div style={{
            fontSize: '0.9rem',
            color: isDarkMode ? '#9ca3af' : '#6b7280',
            marginBottom: '4px'
          }}>
            Current Path:
          </div>
          <div style={{
            fontFamily: 'monospace',
            fontSize: '0.9rem',
            color: isDarkMode ? '#f1f5f9' : '#1f2937',
            backgroundColor: isDarkMode ? '#1f2937' : 'white',
            padding: '8px 12px',
            borderRadius: '6px',
            border: `1px solid ${isDarkMode ? '#4b5563' : '#d1d5db'}`
          }}>
            {currentPath}
          </div>
        </div>

        {/* Directory List */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          maxHeight: '300px'
        }}>
          {loading ? (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              color: isDarkMode ? '#9ca3af' : '#6b7280'
            }}>
              Loading...
            </div>
          ) : error ? (
            <div style={{
              padding: '20px',
              textAlign: 'center',
              color: '#ef4444',
              backgroundColor: '#fef2f2',
              margin: '10px',
              borderRadius: '6px',
              fontSize: '0.9rem'
            }}>
              {error}
            </div>
          ) : items.length === 0 ? (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              color: isDarkMode ? '#9ca3af' : '#6b7280'
            }}>
              No directories found
            </div>
          ) : (
            <div>
              {items.map((item, index) => (
                <div
                  key={index}
                  onClick={() => handleItemClick(item)}
                  style={{
                    padding: '12px 20px',
                    cursor: 'pointer',
                    borderBottom: `1px solid ${isDarkMode ? '#374151' : '#f3f4f6'}`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    backgroundColor: isDarkMode ? '#1e293b' : 'white',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = isDarkMode ? '#374151' : '#f9fafb';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = isDarkMode ? '#1e293b' : 'white';
                  }}
                >
                  <span style={{ fontSize: '1.2rem' }}>
                    {item.is_parent ? '↩️' : '📁'}
                  </span>
                  <span style={{
                    color: isDarkMode ? '#f1f5f9' : '#1f2937',
                    fontSize: '0.9rem'
                  }}>
                    {item.name}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '20px',
          borderTop: `1px solid ${isDarkMode ? '#374151' : '#e5e7eb'}`,
          display: 'flex',
          justifyContent: 'space-between',
          gap: '12px'
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '10px 20px',
              backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
              color: isDarkMode ? '#f1f5f9' : '#374151',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSelectCurrent}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: '500'
            }}
          >
            Select This Directory
          </button>
        </div>
      </div>
    </div>
  );
};

export default DirectoryBrowserModal;