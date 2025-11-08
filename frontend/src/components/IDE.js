import React, { useState, useEffect, useRef } from 'react';

const IDE = ({ initialFiles = {}, onSave, isDarkMode }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const iframeRef = useRef(null);
  const getCodeServerUrl = () => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const directUrl = `${protocol}//${hostname}:8080`;
    const proxyUrl = '/api/code-server';
    return directUrl;
  };
  const codeServerUrl = getCodeServerUrl();
  useEffect(() => {
    const checkCodeServer = async () => {
      try {
        const response = await fetch(codeServerUrl, { method: 'HEAD', mode: 'no-cors' });
        setTimeout(() => setIsLoading(false), 1000);
      } catch (err) {
        setTimeout(() => setIsLoading(false), 2000);
      }
    };
    checkCodeServer();
  }, [codeServerUrl]);
  useEffect(() => {
    if (iframeRef.current) {
      const iframe = iframeRef.current;
      let loadTimeout;
      const handleLoad = () => {
        clearTimeout(loadTimeout);
        setTimeout(() => {
          setIsLoading(false);
          setError(null);
        }, 500);
      };
      const handleError = () => {
        clearTimeout(loadTimeout);
        setIsLoading(false);
        setError('Failed to load VSCode editor. Please ensure code-server is running on port 8080.');
      };
      iframe.addEventListener('load', handleLoad);
      iframe.addEventListener('error', handleError);
      loadTimeout = setTimeout(() => {
        if (isLoading) {
          setIsLoading(false);
          setError('VSCode editor is taking too long to load. Please check if code-server is running.');
        }
      }, 15000);
      return () => {
        iframe.removeEventListener('load', handleLoad);
        iframe.removeEventListener('error', handleError);
        clearTimeout(loadTimeout);
      };
    }
  }, [isLoading, codeServerUrl]);
  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: isDarkMode ? '#0f0f0f' : '#f8fafc'
    }}>
      <div style={{
        height: '40px',
        background: isDarkMode ? '#1a1a1a' : 'white',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            fontSize: '0.9rem',
            fontWeight: '600',
            color: isDarkMode ? '#e2e8f0' : '#1e293b'
          }}>
            VSCode Editor
          </span>
        </div>
      </div>
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {isLoading && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: isDarkMode ? '#1a1a1a' : 'white',
            zIndex: 10
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '16px' }}>⚙️</div>
              <div style={{ color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>Loading VSCode...</div>
            </div>
          </div>
        )}
        {error && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: isDarkMode ? '#1a1a1a' : 'white',
            zIndex: 10
          }}>
            <div style={{ textAlign: 'center', color: '#ef4444' }}>
              <div style={{ fontSize: '2rem', marginBottom: '16px' }}>⚠️</div>
              <div>{error}</div>
            </div>
          </div>
        )}
        <iframe
          ref={iframeRef}
          src={codeServerUrl}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            display: isLoading || error ? 'none' : 'block'
          }}
          title="VSCode Editor"
          allow="clipboard-read; clipboard-write"
        />
      </div>
    </div>
  );
};

export default IDE;