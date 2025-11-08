import React from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage = ({ isDarkMode }) => {
  const navigate = useNavigate();

  const features = [
    {
      icon: '🗂️',
      title: 'Dataset Management',
      description: 'Load and manage KITTI datasets with automatic validation and preview capabilities'
    },
    {
      icon: '⚡',
      title: 'Algorithm Development',
      description: 'Develop and test SLAM algorithms with integrated VSCode editor and real-time debugging'
    },
    {
      icon: '📊',
      title: 'Performance Analysis',
      description: 'Comprehensive trajectory error analysis with ATE, RPE metrics and visualization'
    },
    {
      icon: '🎓',
      title: 'Interactive Tutorials',
      description: 'Learn SLAM concepts through hands-on tutorials with executable code examples'
    },
    {
      icon: '🔬',
      title: 'Algorithm Comparison',
      description: 'Compare multiple SLAM algorithms side-by-side with detailed performance metrics'
    },
    {
      icon: '🎯',
      title: 'Real-time Visualization',
      description: '3D trajectory and point cloud visualization with interactive controls'
    }
  ];

  const quickActions = [
    {
      title: 'Load Dataset',
      description: 'Start by loading a KITTI dataset',
      action: () => navigate('/datasets'),
      color: '#4f46e5'
    },
    {
      title: 'Develop Algorithm',
      description: 'Create or edit SLAM algorithms',
      action: () => navigate('/algorithms'),
      color: '#059669'
    },
    {
      title: 'Learn SLAM',
      description: 'Follow interactive tutorials',
      action: () => navigate('/tutorials'),
      color: '#dc2626'
    }
  ];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      minHeight: '100vh',
      background: isDarkMode 
        ? 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)'
        : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
      color: isDarkMode ? '#e2e8f0' : '#1e293b',
      zIndex: 999,
      overflow: 'auto'
    }}>
      {/* Top Navigation Bar */}
      <div style={{
        position: 'sticky',
        top: 0,
        background: isDarkMode 
          ? 'rgba(15, 23, 42, 0.95)' 
          : 'rgba(248, 250, 252, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 1000
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <img 
            src="/logo.jpg" 
            alt="OpenSLAM Logo"
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              marginRight: '16px',
              objectFit: 'cover'
            }}
          />
          <h1 style={{
            fontSize: '1.5rem',
            fontWeight: '700',
            margin: 0,
            color: isDarkMode ? '#e2e8f0' : '#1e293b'
          }}>
            OpenSLAM
          </h1>
        </div>
        
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <button
            onClick={() => navigate('/datasets')}
            style={{
              padding: '8px 16px',
              background: 'transparent',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '6px',
              color: isDarkMode ? '#e2e8f0' : '#64748b',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
          >
            Get Started
          </button>
          <button
            onClick={() => navigate('/tutorials')}
            style={{
              padding: '8px 16px',
              background: '#4f46e5',
              border: 'none',
              borderRadius: '6px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: '500'
            }}
          >
            Learn SLAM
          </button>
        </div>
      </div>

      {/* Hero Section */}
      <div style={{
        padding: '80px 20px 60px',
        textAlign: 'center',
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '32px'
        }}>
          <img 
            src="/logo.jpg" 
            alt="OpenSLAM Logo"
            style={{
              width: '80px',
              height: '80px',
              borderRadius: '20px',
              marginRight: '24px',
              boxShadow: '0 10px 25px rgba(79, 70, 229, 0.3)',
              objectFit: 'cover'
            }}
          />
          <h1 style={{
            fontSize: '4rem',
            fontWeight: '800',
            margin: 0,
            background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            OpenSLAM
          </h1>
        </div>

        <p style={{
          fontSize: '1.5rem',
          fontWeight: '300',
          marginBottom: '48px',
          maxWidth: '800px',
          margin: '0 auto 48px',
          lineHeight: '1.6',
          opacity: 0.9
        }}>
          Interactive SLAM Platform for Learning, Development, and Research
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '24px',
          marginBottom: '60px'
        }}>
          {quickActions.map((action, index) => (
            <div
              key={index}
              onClick={action.action}
              style={{
                background: isDarkMode ? '#1e293b' : 'white',
                padding: '32px 24px',
                borderRadius: '16px',
                border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: isDarkMode 
                  ? '0 4px 6px rgba(0, 0, 0, 0.3)'
                  : '0 4px 6px rgba(0, 0, 0, 0.1)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = isDarkMode
                  ? '0 12px 25px rgba(0, 0, 0, 0.4)'
                  : '0 12px 25px rgba(0, 0, 0, 0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = isDarkMode
                  ? '0 4px 6px rgba(0, 0, 0, 0.3)'
                  : '0 4px 6px rgba(0, 0, 0, 0.1)';
              }}
            >
              <div style={{
                width: '60px',
                height: '60px',
                background: action.color,
                borderRadius: '12px',
                margin: '0 auto 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ fontSize: '24px', color: 'white' }}>
                  {action.title === 'Load Dataset' ? '📁' : 
                   action.title === 'Develop Algorithm' ? '⚡' : '🎓'}
                </span>
              </div>
              <h3 style={{
                fontSize: '1.25rem',
                fontWeight: '600',
                margin: '0 0 8px 0',
                color: action.color
              }}>
                {action.title}
              </h3>
              <p style={{
                fontSize: '0.9rem',
                margin: 0,
                opacity: 0.8,
                lineHeight: '1.5'
              }}>
                {action.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Features Section */}
      <div style={{
        padding: '60px 20px',
        background: isDarkMode ? 'rgba(30, 41, 59, 0.5)' : 'rgba(248, 250, 252, 0.8)',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h2 style={{
            fontSize: '2.5rem',
            fontWeight: '700',
            textAlign: 'center',
            marginBottom: '48px'
          }}>
            Platform Features
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
            gap: '32px'
          }}>
            {features.map((feature, index) => (
              <div
                key={index}
                style={{
                  background: isDarkMode ? '#1e293b' : 'white',
                  padding: '32px',
                  borderRadius: '16px',
                  border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
                  boxShadow: isDarkMode
                    ? '0 4px 6px rgba(0, 0, 0, 0.3)'
                    : '0 4px 6px rgba(0, 0, 0, 0.1)'
                }}
              >
                <div style={{
                  fontSize: '3rem',
                  marginBottom: '16px'
                }}>
                  {feature.icon}
                </div>
                <h3 style={{
                  fontSize: '1.25rem',
                  fontWeight: '600',
                  marginBottom: '12px',
                  color: isDarkMode ? '#e2e8f0' : '#1e293b'
                }}>
                  {feature.title}
                </h3>
                <p style={{
                  fontSize: '0.95rem',
                  lineHeight: '1.6',
                  margin: 0,
                  opacity: 0.8
                }}>
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        padding: '40px 20px',
        textAlign: 'center',
        borderTop: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        background: isDarkMode ? '#0f172a' : '#f8fafc'
      }}>
        <p style={{
          fontSize: '0.9rem',
          margin: 0,
          opacity: 0.7
        }}>
          OpenSLAM Platform - Interactive SLAM Development Environment
        </p>
      </div>
    </div>
  );
};

export default LandingPage;