import React, { useState, useEffect } from 'react';
import IDE from './IDE';

const AlgorithmDevelopment = ({ algorithms, currentDataset, onAlgorithmCreate, onAlgorithmExecute, onNotification, isDarkMode }) => {
  const [activeTab, setActiveTab] = useState('library');
  const [selectedAlgorithm, setSelectedAlgorithm] = useState(null);
  const [algorithmCode, setAlgorithmCode] = useState('');
  const [algorithmName, setAlgorithmName] = useState('');
  const [algorithmType, setAlgorithmType] = useState('visual_odometry');
  const [executionParameters, setExecutionParameters] = useState({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResults, setExecutionResults] = useState(null);
  const [availableTemplates, setAvailableTemplates] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  const [algorithmLibrary, setAlgorithmLibrary] = useState([]);

  const myAlgorithms = [
    {
      id: 'my_vo_1',
      name: 'Custom Visual Odometry',
      type: 'visual_odometry',
      status: 'draft',
      created_at: '2023-11-01',
      updated_at: '2023-11-05',
      performance: { accuracy: 78, speed: 85 },
      description: 'Custom implementation of feature-based visual odometry'
    },
    {
      id: 'my_slam_1',
      name: 'Modified ORB-SLAM',
      type: 'slam_algorithm',
      status: 'tested',
      created_at: '2023-10-20',
      updated_at: '2023-11-03',
      performance: { accuracy: 92, speed: 80 },
      description: 'ORB-SLAM3 with custom loop closure detection'
    }
  ];

  useEffect(() => {
    loadAlgorithmTemplates();
    loadAlgorithmLibrary();
    // Load default template on mount
    if (!algorithmCode) {
      loadTemplateCode(algorithmType);
    }
  }, []);

  const loadAlgorithmLibrary = async () => {
    try {
      const response = await fetch('/api/algorithms/library');
      if (response.ok) {
        const algorithms = await response.json();
        setAlgorithmLibrary(algorithms);
      } else {
        setAlgorithmLibrary([]);
      }
    } catch (error) {
      onNotification('Error loading algorithm library', 'error');
      setAlgorithmLibrary([]);
    }
  };

  const loadAlgorithmTemplates = async () => {
    try {
      const response = await fetch('/api/algorithm-templates');
      if (response.ok) {
        const templates = await response.json();
        setAvailableTemplates(templates);
      } else {
        // Fallback to mock templates
        setAvailableTemplates([
          { id: 'visual_odometry', name: 'Visual Odometry Template' },
          { id: 'lidar_slam', name: 'LiDAR SLAM Template' },
          { id: 'slam_algorithm', name: 'Generic SLAM Template' }
        ]);
      }
    } catch (error) {
      onNotification('Error loading algorithm templates', 'error');
      // Fallback to mock templates
      setAvailableTemplates([
        { id: 'visual_odometry', name: 'Visual Odometry Template' },
        { id: 'lidar_slam', name: 'LiDAR SLAM Template' },
        { id: 'slam_algorithm', name: 'Generic SLAM Template' }
      ]);
    }
  };

  const loadTemplateCode = async (templateType) => {
    try {
      const response = await fetch(`/api/algorithm-templates/${templateType}`);
      if (response.ok) {
        const template = await response.json();
        setAlgorithmCode(template.skeleton_code || getDefaultTemplate(templateType));
        setExecutionParameters(template.default_parameters || getDefaultParameters(templateType));
      } else {
        setAlgorithmCode(getDefaultTemplate(templateType));
        setExecutionParameters(getDefaultParameters(templateType));
      }
    } catch (error) {
      onNotification('Error loading template', 'error');
      setAlgorithmCode(getDefaultTemplate(templateType));
      setExecutionParameters(getDefaultParameters(templateType));
    }
  };

  const getDefaultTemplate = (type) => {
    const templates = {
      visual_odometry: `import numpy as np
import cv2
from typing import Tuple, List, Optional

class VisualOdometry:
    def __init__(self, camera_matrix: np.ndarray, dist_coeffs: np.ndarray):
        """
        Initialize Visual Odometry system
        
        Args:
            camera_matrix: 3x3 camera intrinsic matrix
            dist_coeffs: distortion coefficients
        """
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.detector = cv2.ORB_create(nfeatures=1000)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # Initialize pose
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        
    def process_frame(self, image: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Process a single frame and estimate motion
        
        Args:
            image: Input grayscale image
            
        Returns:
            pose: 4x4 transformation matrix
            num_matches: number of feature matches
        """
        # Detect and compute features
        keypoints, descriptors = self.detector.detectAndCompute(image, None)
        
        if hasattr(self, 'prev_descriptors') and descriptors is not None:
            # Match features with previous frame
            matches = self.matcher.match(self.prev_descriptors, descriptors)
            matches = sorted(matches, key=lambda x: x.distance)
            
            if len(matches) > 50:  # Minimum matches threshold
                # Extract matched points
                pts1 = np.float32([self.prev_keypoints[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
                pts2 = np.float32([keypoints[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
                
                # Estimate essential matrix
                E, mask = cv2.findEssentialMat(pts1, pts2, self.camera_matrix, method=cv2.RANSAC, prob=0.999, threshold=1.0)
                
                if E is not None:
                    # Recover pose
                    _, R, t, _ = cv2.recoverPose(E, pts1, pts2, self.camera_matrix)
                    
                    # Create transformation matrix
                    T = np.eye(4)
                    T[:3, :3] = R
                    T[:3, 3] = t.flatten()
                    
                    # Update current pose
                    self.current_pose = self.current_pose @ T
                    self.trajectory.append(self.current_pose.copy())
                    
                    num_matches = np.sum(mask)
                else:
                    num_matches = 0
            else:
                num_matches = len(matches)
        else:
            num_matches = 0
            
        # Store current frame data for next iteration
        self.prev_keypoints = keypoints
        self.prev_descriptors = descriptors
        
        return self.current_pose, num_matches
        
    def get_trajectory(self) -> List[np.ndarray]:
        """Get the complete trajectory"""
        return self.trajectory
        
    def reset(self):
        """Reset the odometry system"""
        self.current_pose = np.eye(4)
        self.trajectory = [self.current_pose.copy()]
        if hasattr(self, 'prev_keypoints'):
            delattr(self, 'prev_keypoints')
        if hasattr(self, 'prev_descriptors'):
            delattr(self, 'prev_descriptors')

# Example usage:
# vo = VisualOdometry(camera_matrix, dist_coeffs)
# for frame in frames:
#     pose, matches = vo.process_frame(frame)
#     print(f"Pose: {pose[:3, 3]}, Matches: {matches}")`,
      
      lidar_slam: `import numpy as np
from typing import List, Tuple, Optional
import open3d as o3d

class LiDARSLAM:
    def __init__(self, voxel_size: float = 0.1, max_correspondence_distance: float = 0.5):
        """
        Initialize LiDAR SLAM system
        
        Args:
            voxel_size: voxel size for downsampling
            max_correspondence_distance: maximum distance for ICP correspondence
        """
        self.voxel_size = voxel_size
        self.max_correspondence_distance = max_correspondence_distance
        
        # Initialize pose and map
        self.current_pose = np.eye(4)
        self.global_map = o3d.geometry.PointCloud()
        self.trajectory = [self.current_pose.copy()]
        
        # ICP parameters
        self.icp_threshold = max_correspondence_distance
        self.icp_max_iteration = 50
        
    def preprocess_pointcloud(self, points: np.ndarray) -> o3d.geometry.PointCloud:
        """
        Preprocess point cloud data
        
        Args:
            points: Nx3 numpy array of 3D points
            
        Returns:
            processed point cloud
        """
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        # Remove outliers
        pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
        
        # Downsample
        pcd = pcd.voxel_down_sample(self.voxel_size)
        
        # Estimate normals
        pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        
        return pcd
        
    def process_scan(self, points: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Process a single LiDAR scan
        
        Args:
            points: Nx3 numpy array of 3D points
            
        Returns:
            pose: 4x4 transformation matrix
            fitness: ICP fitness score
        """
        # Preprocess current scan
        current_pcd = self.preprocess_pointcloud(points)
        
        if len(self.global_map.points) > 0:
            # Perform ICP registration
            reg_p2p = o3d.pipelines.registration.registration_icp(
                current_pcd, self.global_map,
                self.max_correspondence_distance,
                np.eye(4),
                o3d.pipelines.registration.TransformationEstimationPointToPoint(),
                o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=self.icp_max_iteration)
            )
            
            # Update pose
            transformation = reg_p2p.transformation
            self.current_pose = self.current_pose @ transformation
            fitness = reg_p2p.fitness
            
            # Transform current scan to global frame
            current_pcd.transform(self.current_pose)
            
            # Add to global map
            self.global_map += current_pcd
            
            # Downsample global map to maintain efficiency
            self.global_map = self.global_map.voxel_down_sample(self.voxel_size)
            
        else:
            # First scan - initialize map
            current_pcd.transform(self.current_pose)
            self.global_map = current_pcd
            fitness = 1.0
            
        self.trajectory.append(self.current_pose.copy())
        
        return self.current_pose, fitness
        
    def get_trajectory(self) -> List[np.ndarray]:
        """Get the complete trajectory"""
        return self.trajectory
        
    def get_map(self) -> o3d.geometry.PointCloud:
        """Get the global map"""
        return self.global_map
        
    def reset(self):
        """Reset the SLAM system"""
        self.current_pose = np.eye(4)
        self.global_map = o3d.geometry.PointCloud()
        self.trajectory = [self.current_pose.copy()]

# Example usage:
# slam = LiDARSLAM(voxel_size=0.1)
# for scan in lidar_scans:
#     pose, fitness = slam.process_scan(scan)
#     print(f"Pose: {pose[:3, 3]}, Fitness: {fitness}")`,
      
      slam_algorithm: `import numpy as np
from typing import Dict, List, Tuple, Optional, Any

class GenericSLAM:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Generic SLAM system
        
        Args:
            config: configuration dictionary with algorithm parameters
        """
        self.config = config
        
        # Initialize state
        self.current_pose = np.eye(4)
        self.landmarks = {}
        self.trajectory = [self.current_pose.copy()]
        
        # Algorithm parameters
        self.feature_threshold = config.get('feature_threshold', 0.01)
        self.max_features = config.get('max_features', 1000)
        self.loop_closure_threshold = config.get('loop_closure_threshold', 0.1)
        
    def extract_features(self, sensor_data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Extract features from sensor data
        
        Args:
            sensor_data: dictionary containing sensor measurements
            
        Returns:
            extracted features
        """
        features = {}
        
        # Process different sensor types
        if 'image' in sensor_data:
            # Extract visual features (placeholder)
            image = sensor_data['image']
            # TODO: Implement feature extraction
            features['visual'] = np.random.rand(100, 2)  # Placeholder
            
        if 'lidar' in sensor_data:
            # Extract LiDAR features (placeholder)
            lidar = sensor_data['lidar']
            # TODO: Implement LiDAR feature extraction
            features['lidar'] = np.random.rand(50, 3)  # Placeholder
            
        return features
        
    def predict_motion(self, control_input: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Predict robot motion based on motion model
        
        Args:
            control_input: control commands (optional)
            
        Returns:
            predicted pose
        """
        # Simple constant velocity model (placeholder)
        if hasattr(self, 'prev_pose'):
            # Estimate velocity from previous poses
            velocity = self.current_pose @ np.linalg.inv(self.prev_pose)
            predicted_pose = self.current_pose @ velocity
        else:
            predicted_pose = self.current_pose.copy()
            
        return predicted_pose
        
    def update_pose(self, observations: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Update pose estimate based on observations
        
        Args:
            observations: sensor observations
            
        Returns:
            updated pose
        """
        # Extract features
        features = self.extract_features(observations)
        
        # Data association and pose update (placeholder)
        # TODO: Implement proper SLAM update equations
        
        # Simple pose update based on feature matching
        if len(features) > 0:
            # Placeholder: add small random motion
            noise = np.random.normal(0, 0.01, (4, 4))
            noise[3, :] = 0
            noise[:, 3] = 0
            noise[3, 3] = 0
            
            self.current_pose = self.current_pose + noise
            
        return self.current_pose
        
    def detect_loop_closure(self) -> Optional[int]:
        """
        Detect loop closures in the trajectory
        
        Returns:
            index of loop closure frame (if detected)
        """
        # Simple distance-based loop closure detection
        current_position = self.current_pose[:3, 3]
        
        for i, pose in enumerate(self.trajectory[:-10]):  # Skip recent poses
            position = pose[:3, 3]
            distance = np.linalg.norm(current_position - position)
            
            if distance < self.loop_closure_threshold:
                return i
                
        return None
        
    def process_frame(self, sensor_data: Dict[str, np.ndarray]) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a single frame of sensor data
        
        Args:
            sensor_data: dictionary containing all sensor measurements
            
        Returns:
            pose: updated pose estimate
            info: additional information about processing
        """
        # Store previous pose
        self.prev_pose = self.current_pose.copy()
        
        # Predict motion
        predicted_pose = self.predict_motion()
        
        # Update pose based on observations
        self.current_pose = self.update_pose(sensor_data)
        
        # Detect loop closures
        loop_closure_idx = self.detect_loop_closure()
        
        # Add to trajectory
        self.trajectory.append(self.current_pose.copy())
        
        # Prepare info
        info = {
            'loop_closure': loop_closure_idx is not None,
            'loop_closure_idx': loop_closure_idx,
            'num_features': len(self.extract_features(sensor_data)),
            'prediction_error': np.linalg.norm(predicted_pose[:3, 3] - self.current_pose[:3, 3])
        }
        
        return self.current_pose, info
        
    def get_trajectory(self) -> List[np.ndarray]:
        """Get the complete trajectory"""
        return self.trajectory
        
    def get_landmarks(self) -> Dict[int, np.ndarray]:
        """Get the landmark map"""
        return self.landmarks
        
    def reset(self):
        """Reset the SLAM system"""
        self.current_pose = np.eye(4)
        self.landmarks = {}
        self.trajectory = [self.current_pose.copy()]
        if hasattr(self, 'prev_pose'):
            delattr(self, 'prev_pose')

# Example usage:
# config = {'feature_threshold': 0.01, 'max_features': 1000}
# slam = GenericSLAM(config)
# for frame_data in sensor_frames:
#     pose, info = slam.process_frame(frame_data)
#     print(f"Pose: {pose[:3, 3]}, Loop closure: {info['loop_closure']}")`
    };
    return templates[type] || templates['slam_algorithm'];
  };

  const getDefaultParameters = (type) => {
    const params = {
      visual_odometry: {
        'max_features': 1000,
        'match_threshold': 0.7,
        'ransac_threshold': 1.0,
        'min_matches': 50
      },
      lidar_slam: {
        'voxel_size': 0.1,
        'max_correspondence_distance': 0.5,
        'icp_max_iteration': 50,
        'outlier_std_ratio': 2.0
      },
      slam_algorithm: {
        'feature_threshold': 0.01,
        'max_features': 1000,
        'loop_closure_threshold': 0.1,
        'motion_noise': 0.01
      }
    };
    return params[type] || params['slam_algorithm'];
  };

  const filteredLibrary = algorithmLibrary.filter(alg => 
    alg.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    alg.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
    alg.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const renderLibraryTab = () => (
    <div style={{ padding: '12px', height: '100%', overflow: 'auto' }}>
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '12px',
        alignItems: 'center',
        flexWrap: 'wrap'
      }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <input
            type="text"
            placeholder="Search algorithms..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '6px 8px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '4px',
              background: isDarkMode ? '#334155' : 'white',
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              fontSize: '0.8rem'
            }}
          />
        </div>
        <select style={{
          padding: '6px 8px',
          border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
          borderRadius: '4px',
          background: isDarkMode ? '#334155' : 'white',
          color: isDarkMode ? '#e2e8f0' : '#1e293b',
          fontSize: '0.8rem'
        }}>
          <option>All Categories</option>
          <option>Visual SLAM</option>
          <option>LiDAR SLAM</option>
          <option>Visual-Inertial SLAM</option>
          <option>RGB-D SLAM</option>
        </select>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '12px'
      }}>
        {filteredLibrary.map(algorithm => (
          <div key={algorithm.id} style={{
            background: isDarkMode ? '#1a1a1a' : 'white',
            border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
            borderRadius: '8px',
            padding: '12px',
            boxShadow: isDarkMode 
              ? '0 1px 3px rgba(0,0,0,0.3)' 
              : '0 1px 3px rgba(0,0,0,0.1)',
            transition: 'all 0.2s ease',
            cursor: 'pointer'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = isDarkMode 
              ? '0 4px 12px rgba(0,0,0,0.4)' 
              : '0 4px 12px rgba(0,0,0,0.15)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = isDarkMode 
              ? '0 1px 3px rgba(0,0,0,0.3)' 
              : '0 1px 3px rgba(0,0,0,0.1)';
          }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div>
                <h3 style={{ 
                  margin: '0 0 4px 0', 
                  fontSize: '1.1rem', 
                  fontWeight: '600',
                  color: isDarkMode ? '#e2e8f0' : '#1e293b'
                }}>
                  {algorithm.name}
                </h3>
                <span style={{
                  fontSize: '0.8rem',
                  color: '#4f46e5',
                  background: isDarkMode ? 'rgba(79, 70, 229, 0.2)' : 'rgba(79, 70, 229, 0.1)',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontWeight: '500'
                }}>
                  {algorithm.category}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ fontSize: '0.8rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>📦</span>
                <span style={{ fontSize: '0.8rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                  Plugin
                </span>
              </div>
            </div>

            {/* Description */}
            <p style={{
              margin: '0 0 16px 0',
              fontSize: '0.85rem',
              color: isDarkMode ? '#94a3b8' : '#64748b',
              lineHeight: '1.4'
            }}>
              {algorithm.description}
            </p>

            {/* Algorithm Info */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                <span>Version: {algorithm.version || '1.0.0'}</span>
                <span>•</span>
                <span>License: {algorithm.license || 'Unknown'}</span>
                <span>•</span>
                <span>Language: {algorithm.language || 'Python'}</span>
              </div>
            </div>

            {/* Tags */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
              {(algorithm.tags || []).slice(0, 4).map(tag => (
                <span key={tag} style={{
                  fontSize: '0.7rem',
                  background: isDarkMode ? '#334155' : '#f1f5f9',
                  color: isDarkMode ? '#94a3b8' : '#64748b',
                  padding: '2px 6px',
                  borderRadius: '6px',
                  fontWeight: '500'
                }}>
                  {tag}
                </span>
              ))}
            </div>

            {/* Footer */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                <span>Author: {algorithm.author}</span>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  onClick={() => {
                    setSelectedAlgorithm(algorithm);
                    onNotification(`Viewing details for ${algorithm.name}`, 'info');
                  }}
                  style={{
                    padding: '4px 8px',
                    border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                    background: 'transparent',
                    color: isDarkMode ? '#e2e8f0' : '#64748b',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                >
                  View Details
                </button>
                <button 
                  onClick={async () => {
                    try {
                      const response = await fetch(`/api/algorithms/${algorithm.plugin_id}/load`, {
                        method: 'POST'
                      });
                      if (response.ok) {
                        onNotification(`${algorithm.name} loaded successfully`, 'success');
                      } else {
                        onNotification(`Failed to load ${algorithm.name}`, 'error');
                      }
                    } catch (error) {
                      onNotification(`Error loading ${algorithm.name}`, 'error');
                    }
                  }}
                  style={{
                    padding: '4px 8px',
                    border: 'none',
                    background: '#4f46e5',
                    color: 'white',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                >
                  Load Algorithm
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderMyAlgorithmsTab = () => (
    <div style={{ padding: '12px', height: '100%', overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <h3 style={{ margin: 0, color: isDarkMode ? '#e2e8f0' : '#1e293b', fontSize: '1rem' }}>My Algorithms</h3>
        <button 
          onClick={() => setActiveTab('editor')}
          style={{
            padding: '6px 12px',
            background: '#4f46e5',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '0.8rem',
            fontWeight: '500',
            cursor: 'pointer'
          }}
        >
          + New Algorithm
        </button>
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
        gap: '12px'
      }}>
        {myAlgorithms.map(algorithm => (
          <div key={algorithm.id} style={{
            background: isDarkMode ? '#1a1a1a' : 'white',
            border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
            borderRadius: '6px',
            padding: '12px',
            cursor: 'pointer'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <h4 style={{ margin: 0, fontSize: '1rem', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                {algorithm.name}
              </h4>
              <span style={{
                fontSize: '0.7rem',
                padding: '2px 6px',
                borderRadius: '6px',
                background: algorithm.status === 'tested' ? '#22c55e' : '#f59e0b',
                color: 'white',
                fontWeight: '500'
              }}>
                {algorithm.status}
              </span>
            </div>
            <p style={{ 
              margin: '0 0 12px 0', 
              fontSize: '0.8rem', 
              color: isDarkMode ? '#94a3b8' : '#64748b' 
            }}>
              {algorithm.description}
            </p>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                Modified: {new Date(algorithm.updated_at).toLocaleDateString()}
              </span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button 
                  onClick={() => {
                    setSelectedAlgorithm(algorithm);
                    setAlgorithmName(algorithm.name);
                    setAlgorithmType(algorithm.type);
                    setAlgorithmCode(algorithm.code || getDefaultTemplate(algorithm.type));
                    setExecutionParameters(algorithm.parameters || getDefaultParameters(algorithm.type));
                    setActiveTab('editor');
                  }}
                  style={{
                    padding: '4px 8px',
                    border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
                    background: 'transparent',
                    color: isDarkMode ? '#e2e8f0' : '#64748b',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    cursor: 'pointer'
                  }}
                >
                  Edit
                </button>
                <button 
                  onClick={() => {
                    if (!currentDataset) {
                      onNotification('Please select a dataset first', 'error');
                      return;
                    }
                    setIsExecuting(true);
                    // Simulate algorithm execution
                    setTimeout(() => {
                      setExecutionResults({
                        success: true,
                        execution_time: Math.random() * 10 + 5,
                        frames_processed: currentDataset.sequence_length || 1000,
                        metrics: {
                          ate: Math.random() * 0.5,
                          rpe_trans: Math.random() * 0.1,
                          rpe_rot: Math.random() * 0.05
                        }
                      });
                      setIsExecuting(false);
                      onNotification(`${algorithm.name} executed successfully`, 'success');
                      setActiveTab('benchmark');
                    }, 2000);
                  }}
                  disabled={isExecuting}
                  style={{
                    padding: '4px 8px',
                    border: 'none',
                    background: isExecuting ? '#94a3b8' : '#4f46e5',
                    color: 'white',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    cursor: isExecuting ? 'not-allowed' : 'pointer'
                  }}
                >
                  {isExecuting ? 'Running...' : 'Run'}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const [iframeScale, setIframeScale] = useState(0.7);
  const [iframeSize, setIframeSize] = useState({ width: '140%', height: '140%' });

  useEffect(() => {
    const calculateScale = () => {
      const viewportHeight = window.innerHeight;
      const viewportWidth = window.innerWidth;
      const headerHeight = 250;
      const availableHeight = viewportHeight - headerHeight;
      const availableWidth = viewportWidth;
      const minVSCodeHeight = 400;
      const minVSCodeWidth = 1400;
      const scaleY = availableHeight / minVSCodeHeight;
      const scaleX = availableWidth / minVSCodeWidth;
      const scale = Math.min(scaleY, scaleX, 1);
      const finalScale = Math.max(scale, 0.4);
      setIframeScale(finalScale);
      setIframeSize({
        width: `${100 / finalScale}%`,
        height: `${100 / finalScale}%`
      });
    };
    calculateScale();
    window.addEventListener('resize', calculateScale);
    return () => window.removeEventListener('resize', calculateScale);
  }, []);

  const renderEditorTab = () => (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        padding: '4px 8px',
        background: isDarkMode ? '#2d2d2d' : '#f8fafc',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '4px',
        minHeight: '40px'
      }}>
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Algorithm name"
            value={algorithmName}
            onChange={(e) => setAlgorithmName(e.target.value)}
            style={{
              padding: '2px 6px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '3px',
              background: isDarkMode ? '#334155' : 'white',
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              fontSize: '0.7rem',
              minWidth: '100px'
            }}
          />
          <select
            value={algorithmType}
            onChange={(e) => {
              setAlgorithmType(e.target.value);
              loadTemplateCode(e.target.value);
            }}
            style={{
              padding: '2px 6px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              borderRadius: '3px',
              background: isDarkMode ? '#334155' : 'white',
              color: isDarkMode ? '#e2e8f0' : '#1e293b',
              fontSize: '0.7rem'
            }}
          >
            <option value="visual_odometry">Visual Odometry</option>
            <option value="lidar_slam">LiDAR SLAM</option>
            <option value="slam_algorithm">Generic SLAM</option>
          </select>
        </div>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button 
            onClick={() => {
              window.open('http://localhost:8080', '_blank', 'width=1200,height=800');
            }}
            style={{
              padding: '2px 6px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              background: 'transparent',
              color: isDarkMode ? '#e2e8f0' : '#64748b',
              borderRadius: '3px',
              fontSize: '0.65rem',
              cursor: 'pointer'
            }}
          >
            VSCode
          </button>
          <button 
            onClick={() => {
              if (!algorithmCode.trim()) {
                onNotification('No code to validate', 'error');
                return;
              }
              setTimeout(() => {
                const isValid = Math.random() > 0.3;
                if (isValid) {
                  onNotification('Code validation successful', 'success');
                } else {
                  onNotification('Validation errors: Syntax error on line 42', 'error');
                }
              }, 1000);
            }}
            style={{
              padding: '2px 6px',
              border: `1px solid ${isDarkMode ? '#475569' : '#d1d5db'}`,
              background: 'transparent',
              color: isDarkMode ? '#e2e8f0' : '#64748b',
              borderRadius: '3px',
              fontSize: '0.65rem',
              cursor: 'pointer'
            }}
          >
            Validate
          </button>
          <button 
            onClick={() => {
              if (!algorithmName.trim()) {
                onNotification('Algorithm name is required', 'error');
                return;
              }
              if (!algorithmCode.trim()) {
                onNotification('Algorithm code is required', 'error');
                return;
              }
              const newAlgorithm = {
                id: `alg_${Date.now()}`,
                name: algorithmName,
                type: algorithmType,
                code: algorithmCode,
                parameters: executionParameters,
                status: 'draft',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                description: `Custom ${algorithmType.replace('_', ' ')} implementation`
              };
              onAlgorithmCreate(newAlgorithm);
              setSelectedAlgorithm(newAlgorithm);
              onNotification(`Algorithm ${algorithmName} saved successfully`, 'success');
            }}
            style={{
              padding: '2px 6px',
              border: 'none',
              background: '#4f46e5',
              color: 'white',
              borderRadius: '3px',
              fontSize: '0.65rem',
              cursor: 'pointer'
            }}
          >
            Save
          </button>
        </div>
      </div>
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <iframe
          src="http://localhost:8080"
          style={{
            width: iframeSize.width,
            height: iframeSize.height,
            border: 'none',
            transform: `scale(${iframeScale})`,
            transformOrigin: 'top left'
          }}
          title="VSCode Editor"
        />
      </div>
    </div>
  );

  const renderBenchmarkTab = () => (
    <div style={{ padding: '12px', height: '100%', overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <h3 style={{ margin: 0, color: isDarkMode ? '#e2e8f0' : '#1e293b', fontSize: '1rem' }}>
          Algorithm Benchmarks
        </h3>
        {currentDataset && (
          <span style={{ 
            fontSize: '0.8rem', 
            color: isDarkMode ? '#94a3b8' : '#64748b',
            background: isDarkMode ? '#334155' : '#f1f5f9',
            padding: '3px 6px',
            borderRadius: '4px'
          }}>
            Dataset: {currentDataset.name}
          </span>
        )}
      </div>

      {executionResults ? (
        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '6px',
          padding: '12px'
        }}>
          <h4 style={{ margin: '0 0 8px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b', fontSize: '0.9rem' }}>
            Latest Execution Results
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '8px', marginBottom: '12px' }}>
            <div style={{
              background: isDarkMode ? '#334155' : '#f8fafc',
              padding: '8px',
              borderRadius: '4px'
            }}>
              <div style={{ fontSize: '0.7rem', color: isDarkMode ? '#94a3b8' : '#64748b', marginBottom: '2px' }}>
                Status
              </div>
              <div style={{ 
                fontSize: '0.9rem', 
                fontWeight: '600',
                color: executionResults.success ? '#22c55e' : '#ef4444'
              }}>
                {executionResults.success ? 'Success' : 'Failed'}
              </div>
            </div>
            
            <div style={{
              background: isDarkMode ? '#334155' : '#f8fafc',
              padding: '8px',
              borderRadius: '4px'
            }}>
              <div style={{ fontSize: '0.7rem', color: isDarkMode ? '#94a3b8' : '#64748b', marginBottom: '2px' }}>
                Execution Time
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: '600', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                {executionResults.execution_time?.toFixed(2)}s
              </div>
            </div>
            <div style={{
              background: isDarkMode ? '#334155' : '#f8fafc',
              padding: '8px',
              borderRadius: '4px'
            }}>
              <div style={{ fontSize: '0.7rem', color: isDarkMode ? '#94a3b8' : '#64748b', marginBottom: '2px' }}>
                Frames Processed
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: '600', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                {executionResults.frames_processed?.toLocaleString()}
              </div>
            </div>
          </div>

          {executionResults.metrics && (
            <div>
              <h5 style={{ margin: '0 0 12px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                Performance Metrics
              </h5>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
                <div style={{
                  background: isDarkMode ? '#334155' : '#f8fafc',
                  padding: '10px',
                  borderRadius: '6px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                    ATE (Absolute Trajectory Error)
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: '600', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                    {executionResults.metrics.ate?.toFixed(4)}m
                  </div>
                </div>
                
                <div style={{
                  background: isDarkMode ? '#334155' : '#f8fafc',
                  padding: '10px',
                  borderRadius: '6px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                    RPE Translation
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: '600', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                    {executionResults.metrics.rpe_trans?.toFixed(4)}m
                  </div>
                </div>
                
                <div style={{
                  background: isDarkMode ? '#334155' : '#f8fafc',
                  padding: '10px',
                  borderRadius: '6px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '0.75rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                    RPE Rotation
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: '600', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
                    {executionResults.metrics.rpe_rot?.toFixed(4)}rad
                  </div>
                </div>
              </div>
            </div>
          )}

          {executionResults.error && (
            <div style={{ marginTop: '16px' }}>
              <h5 style={{ margin: '0 0 8px 0', color: '#ef4444' }}>Error Details</h5>
              <pre style={{
                background: isDarkMode ? '#1f2937' : '#fef2f2',
                color: isDarkMode ? '#fca5a5' : '#dc2626',
                padding: '12px',
                borderRadius: '6px',
                fontSize: '0.8rem',
                overflow: 'auto'
              }}>
                {executionResults.error}
              </pre>
            </div>
          )}
        </div>
      ) : (
        <div style={{
          background: isDarkMode ? '#1a1a1a' : 'white',
          border: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
          borderRadius: '8px',
          padding: '40px 20px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px', opacity: 0.3 }}>📊</div>
          <h4 style={{ margin: '0 0 8px 0', color: isDarkMode ? '#e2e8f0' : '#1e293b' }}>
            No Benchmark Results Yet
          </h4>
          <p style={{ margin: 0, color: isDarkMode ? '#94a3b8' : '#64748b' }}>
            Run an algorithm on a dataset to see performance metrics and benchmarks here.
          </p>
        </div>
      )}
    </div>
  );

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: isDarkMode ? '#0f0f0f' : '#f8fafc',
      color: isDarkMode ? '#e0e0e0' : '#1e293b',
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '8px 12px',
        background: isDarkMode ? '#1a1a1a' : 'white',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`
      }}>
        <h1 style={{ margin: '0 0 2px 0', fontSize: '1.2rem', fontWeight: '600' }}>
          Algorithm Development
        </h1>
        <p style={{ margin: 0, color: isDarkMode ? '#94a3b8' : '#64748b', fontSize: '0.8rem' }}>
          Explore, develop, and benchmark SLAM algorithms
        </p>
      </div>
      <div style={{
        display: 'flex',
        background: isDarkMode ? '#1a1a1a' : 'white',
        borderBottom: `1px solid ${isDarkMode ? '#334155' : '#e2e8f0'}`,
        overflowX: 'auto'
      }}>
        {[
          { id: 'library', label: 'Algorithm Library', icon: '📚' },
          { id: 'my-algorithms', label: 'My Algorithms', icon: '🔧' },
          { id: 'editor', label: 'Code Editor', icon: '💻' },
          { id: 'benchmark', label: 'Benchmarks', icon: '📊' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '8px 12px',
              border: 'none',
              background: activeTab === tab.id 
                ? (isDarkMode ? '#334155' : '#f1f5f9') 
                : 'transparent',
              color: activeTab === tab.id 
                ? (isDarkMode ? '#e2e8f0' : '#4f46e5') 
                : (isDarkMode ? '#94a3b8' : '#64748b'),
              borderBottom: activeTab === tab.id ? '2px solid #4f46e5' : '2px solid transparent',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: '500',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease',
              whiteSpace: 'nowrap'
            }}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {activeTab === 'library' && renderLibraryTab()}
        {activeTab === 'my-algorithms' && renderMyAlgorithmsTab()}
        {activeTab === 'editor' && renderEditorTab()}
        {activeTab === 'benchmark' && renderBenchmarkTab()}
      </div>
    </div>
  );
};

export default AlgorithmDevelopment;