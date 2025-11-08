import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navigation = ({ isConnected, currentDataset, onDatasetSelect, isDarkMode, onToggleTheme, collapsed, onToggleCollapse }) => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigationItems = [
    { path: '/', label: 'Home', icon: '🏠' },
    { path: '/datasets', label: 'Datasets', icon: '🗂️' },
    { path: '/dataset-preview', label: 'Preview', icon: '👁️' },
    { path: '/algorithms', label: 'Algorithms', icon: '⚡' },
    { path: '/visualization', label: 'Visualization', icon: '📊' },
    { path: '/tutorials', label: 'Tutorials', icon: '🎓' },
    { path: '/analysis', label: 'Analysis', icon: '🔬' }
  ];

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <>
      {/* Desktop Sidebar */}
      <div style={{
        width: collapsed ? '60px' : '250px',
        height: '100vh',
        background: isDarkMode ? '#1a1a1a' : 'white',
        borderRight: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 1000,
        transition: 'width 0.3s ease',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: collapsed ? '16px 8px' : '16px 20px',
          borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          {!collapsed && (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{
                width: '32px',
                height: '32px',
                background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: '12px'
              }}>
                <span style={{ fontSize: '16px', color: 'white' }}>🗺️</span>
              </div>
              <h1 style={{
                fontSize: '1.25rem',
                fontWeight: '700',
                margin: 0,
                color: isDarkMode ? '#e2e8f0' : '#1e293b'
              }}>
                OpenSLAM
              </h1>
            </div>
          )}
          
          <button
            onClick={onToggleCollapse}
            style={{
              background: 'none',
              border: 'none',
              color: isDarkMode ? '#94a3b8' : '#64748b',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '4px',
              fontSize: '18px'
            }}
          >
            {collapsed ? '→' : '←'}
          </button>
        </div>

        {/* Connection Status */}
        <div style={{
          padding: collapsed ? '8px' : '12px 20px',
          borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isConnected ? '#22c55e' : '#ef4444',
              marginRight: collapsed ? 0 : '8px'
            }} />
            {!collapsed && (
              <span style={{
                fontSize: '0.8rem',
                color: isDarkMode ? '#94a3b8' : '#64748b'
              }}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            )}
          </div>
        </div>

        {/* Navigation Items */}
        <nav style={{ flex: 1, padding: '16px 0' }}>
          {navigationItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: collapsed ? '12px 16px' : '12px 20px',
                  color: isActive 
                    ? '#4f46e5' 
                    : (isDarkMode ? '#e2e8f0' : '#64748b'),
                  textDecoration: 'none',
                  background: isActive 
                    ? (isDarkMode ? 'rgba(79, 70, 229, 0.1)' : 'rgba(79, 70, 229, 0.05)')
                    : 'transparent',
                  borderRight: isActive ? '3px solid #4f46e5' : 'none',
                  transition: 'all 0.2s ease',
                  justifyContent: collapsed ? 'center' : 'flex-start'
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
                <span style={{ 
                  fontSize: '18px',
                  marginRight: collapsed ? 0 : '12px'
                }}>
                  {item.icon}
                </span>
                {!collapsed && (
                  <span style={{ 
                    fontSize: '0.9rem',
                    fontWeight: isActive ? '600' : '400'
                  }}>
                    {item.label}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Theme Toggle */}
        <div style={{
          padding: collapsed ? '16px 8px' : '16px 20px',
          borderTop: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
        }}>
          <button
            onClick={onToggleTheme}
            style={{
              width: '100%',
              padding: '8px',
              background: isDarkMode ? '#334155' : '#f1f5f9',
              border: 'none',
              borderRadius: '6px',
              color: isDarkMode ? '#e2e8f0' : '#64748b',
              cursor: 'pointer',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: collapsed ? 'center' : 'flex-start'
            }}
          >
            <span style={{ 
              fontSize: '16px',
              marginRight: collapsed ? 0 : '8px'
            }}>
              {isDarkMode ? '☀️' : '🌙'}
            </span>
            {!collapsed && (isDarkMode ? 'Light Mode' : 'Dark Mode')}
          </button>
        </div>
      </div>

      {/* Mobile Header */}
      <div style={{
        display: 'none',
        '@media (max-width: 768px)': {
          display: 'block'
        }
      }} className="mobile-header">
        <div style={{
          height: '60px',
          background: isDarkMode ? '#1a1a1a' : 'white',
          borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1001
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <img 
              src="/logo.jpg" 
              alt="OpenSLAM Logo"
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                marginRight: '12px',
                objectFit: 'cover'
              }}
            />
            <h1 style={{
              fontSize: '1.25rem',
              fontWeight: '700',
              margin: 0,
              color: isDarkMode ? '#e2e8f0' : '#1e293b'
            }}>
              OpenSLAM
            </h1>
          </div>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{
              background: 'none',
              border: 'none',
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              cursor: 'pointer',
              padding: '8px',
              fontSize: '24px'
            }}
          >
            {mobileMenuOpen ? '✕' : '☰'}
          </button>
        </div>

        {/* Mobile Menu Overlay */}
        {mobileMenuOpen && (
          <div style={{
            position: 'fixed',
            top: '60px',
            left: 0,
            right: 0,
            bottom: 0,
            background: isDarkMode ? 'rgba(15, 23, 42, 0.95)' : 'rgba(248, 250, 252, 0.95)',
            backdropFilter: 'blur(10px)',
            zIndex: 1000,
            padding: '20px'
          }}>
            <nav>
              {navigationItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={closeMobileMenu}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '16px 20px',
                      color: isActive 
                        ? '#4f46e5' 
                        : (isDarkMode ? '#e2e8f0' : '#64748b'),
                      textDecoration: 'none',
                      background: isActive 
                        ? (isDarkMode ? 'rgba(79, 70, 229, 0.1)' : 'rgba(79, 70, 229, 0.05)')
                        : 'transparent',
                      borderRadius: '8px',
                      marginBottom: '8px',
                      fontSize: '1.1rem'
                    }}
                  >
                    <span style={{ fontSize: '20px', marginRight: '16px' }}>
                      {item.icon}
                    </span>
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            <div style={{ marginTop: '32px' }}>
              <button
                onClick={() => {
                  onToggleTheme();
                  closeMobileMenu();
                }}
                style={{
                  width: '100%',
                  padding: '16px',
                  background: isDarkMode ? '#334155' : '#f1f5f9',
                  border: 'none',
                  borderRadius: '8px',
                  color: isDarkMode ? '#e2e8f0' : '#64748b',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <span style={{ fontSize: '20px', marginRight: '12px' }}>
                  {isDarkMode ? '☀️' : '🌙'}
                </span>
                {isDarkMode ? 'Light Mode' : 'Dark Mode'}
              </button>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        @media (max-width: 768px) {
          .mobile-header {
            display: block !important;
          }
        }
      `}</style>
    </>
  );
};

export default Navigation;