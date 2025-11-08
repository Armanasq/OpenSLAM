import sys
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from scipy.spatial.transform import Rotation as R
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
@dataclass
class IMUMeasurement:
    timestamp: float
    acceleration: np.ndarray
    angular_velocity: np.ndarray
    temperature: Optional[float] = None
@dataclass
class IMUBias:
    accelerometer_bias: np.ndarray
    gyroscope_bias: np.ndarray
    timestamp: float
@dataclass
class IMUState:
    timestamp: float
    position: np.ndarray
    velocity: np.ndarray
    orientation: np.ndarray
    accelerometer_bias: np.ndarray
    gyroscope_bias: np.ndarray
    covariance: np.ndarray
class IMUPreintegrator:
    def __init__(self, gravity: np.ndarray = np.array([0, 0, -9.81]), noise_acc: float = 0.01, noise_gyro: float = 0.001, noise_acc_bias: float = 0.0001, noise_gyro_bias: float = 0.00001):
        self.gravity = gravity
        self.noise_acc = noise_acc
        self.noise_gyro = noise_gyro
        self.noise_acc_bias = noise_acc_bias
        self.noise_gyro_bias = noise_gyro_bias
        self.reset()
    def reset(self):
        self.delta_time = 0.0
        self.delta_position = np.zeros(3)
        self.delta_velocity = np.zeros(3)
        self.delta_rotation = np.eye(3)
        self.jacobian = np.eye(15)
        self.covariance = np.zeros((15, 15))
        self.measurements = []
    def add_measurement(self, measurement: IMUMeasurement, bias: IMUBias):
        if not self.measurements:
            self.start_timestamp = measurement.timestamp
        else:
            dt = measurement.timestamp - self.measurements[-1].timestamp
            self._integrate_measurement(measurement, bias, dt)
        self.measurements.append(measurement)
        self.delta_time = measurement.timestamp - self.start_timestamp
    def _integrate_measurement(self, measurement: IMUMeasurement, bias: IMUBias, dt: float):
        acc_corrected = measurement.acceleration - bias.accelerometer_bias
        gyro_corrected = measurement.angular_velocity - bias.gyroscope_bias
        rotation_increment = self._so3_exp(gyro_corrected * dt)
        self.delta_position += self.delta_velocity * dt + 0.5 * self.delta_rotation @ acc_corrected * dt * dt
        self.delta_velocity += self.delta_rotation @ acc_corrected * dt
        self.delta_rotation = self.delta_rotation @ rotation_increment
        self._update_jacobian_and_covariance(acc_corrected, gyro_corrected, dt)
    def _so3_exp(self, omega: np.ndarray) -> np.ndarray:
        angle = np.linalg.norm(omega)
        if angle < 1e-8:
            return np.eye(3) + self._skew_symmetric(omega)
        axis = omega / angle
        K = self._skew_symmetric(axis)
        return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K
    def _skew_symmetric(self, v: np.ndarray) -> np.ndarray:
        return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    def _update_jacobian_and_covariance(self, acc: np.ndarray, gyro: np.ndarray, dt: float):
        F = np.eye(15)
        F[0:3, 3:6] = np.eye(3) * dt
        F[3:6, 6:9] = -self.delta_rotation @ self._skew_symmetric(acc) * dt
        F[3:6, 9:12] = -self.delta_rotation * dt
        F[6:9, 6:9] = self._so3_exp(-gyro * dt)
        F[6:9, 12:15] = -self._so3_left_jacobian(gyro * dt) * dt
        G = np.zeros((15, 12))
        G[3:6, 0:3] = -self.delta_rotation * dt
        G[6:9, 3:6] = -self._so3_left_jacobian(gyro * dt) * dt
        G[9:12, 6:9] = np.eye(3) * dt
        G[12:15, 9:12] = np.eye(3) * dt
        Q = np.zeros((12, 12))
        Q[0:3, 0:3] = np.eye(3) * self.noise_acc * self.noise_acc
        Q[3:6, 3:6] = np.eye(3) * self.noise_gyro * self.noise_gyro
        Q[6:9, 6:9] = np.eye(3) * self.noise_acc_bias * self.noise_acc_bias
        Q[9:12, 9:12] = np.eye(3) * self.noise_gyro_bias * self.noise_gyro_bias
        self.jacobian = F @ self.jacobian
        self.covariance = F @ self.covariance @ F.T + G @ Q @ G.T
    def _so3_left_jacobian(self, omega: np.ndarray) -> np.ndarray:
        angle = np.linalg.norm(omega)
        if angle < 1e-8:
            return np.eye(3)
        axis = omega / angle
        s = np.sin(angle)
        c = np.cos(angle)
        return (s / angle) * np.eye(3) + (1 - c) / angle * self._skew_symmetric(axis) + (angle - s) / (angle ** 3) * np.outer(axis, axis)
    def get_preintegrated_measurement(self) -> Dict:
        return {'delta_time': self.delta_time, 'delta_position': self.delta_position.copy(), 'delta_velocity': self.delta_velocity.copy(), 'delta_rotation': self.delta_rotation.copy(), 'jacobian': self.jacobian.copy(), 'covariance': self.covariance.copy(), 'num_measurements': len(self.measurements)}
class IMUIntegrator:
    def __init__(self, initial_state: IMUState, gravity: np.ndarray = np.array([0, 0, -9.81])):
        self.state = initial_state
        self.gravity = gravity
        self.preintegrator = IMUPreintegrator(gravity)
    def predict_state(self, measurements: List[IMUMeasurement], bias: IMUBias) -> IMUState:
        self.preintegrator.reset()
        for measurement in measurements:
            self.preintegrator.add_measurement(measurement, bias)
        preint = self.preintegrator.get_preintegrated_measurement()
        dt = preint['delta_time']
        R_i = self.state.orientation
        new_position = self.state.position + self.state.velocity * dt + 0.5 * self.gravity * dt * dt + R_i @ preint['delta_position']
        new_velocity = self.state.velocity + self.gravity * dt + R_i @ preint['delta_velocity']
        new_orientation = R_i @ preint['delta_rotation']
        new_acc_bias = self.state.accelerometer_bias.copy()
        new_gyro_bias = self.state.gyroscope_bias.copy()
        F = np.eye(15)
        F[0:3, 3:6] = np.eye(3) * dt
        F[0:3, 6:9] = R_i @ preint['jacobian'][0:3, 6:9]
        F[0:3, 9:12] = R_i @ preint['jacobian'][0:3, 9:12]
        F[0:3, 12:15] = R_i @ preint['jacobian'][0:3, 12:15]
        F[3:6, 6:9] = R_i @ preint['jacobian'][3:6, 6:9]
        F[3:6, 9:12] = R_i @ preint['jacobian'][3:6, 9:12]
        F[3:6, 12:15] = R_i @ preint['jacobian'][3:6, 12:15]
        F[6:9, 6:9] = preint['jacobian'][6:9, 6:9]
        F[6:9, 12:15] = preint['jacobian'][6:9, 12:15]
        new_covariance = F @ self.state.covariance @ F.T
        new_covariance[0:9, 0:9] += R_i @ preint['covariance'][0:9, 0:9] @ R_i.T
        new_covariance[6:9, 6:9] += preint['covariance'][6:9, 6:9]
        return IMUState(timestamp=measurements[-1].timestamp, position=new_position, velocity=new_velocity, orientation=new_orientation, accelerometer_bias=new_acc_bias, gyroscope_bias=new_gyro_bias, covariance=new_covariance)
    def update_state(self, new_state: IMUState):
        self.state = new_state
class BiasEstimator:
    def __init__(self, window_size: int = 100, convergence_threshold: float = 1e-6):
        self.window_size = window_size
        self.convergence_threshold = convergence_threshold
        self.acc_measurements = []
        self.gyro_measurements = []
        self.current_bias = IMUBias(np.zeros(3), np.zeros(3), 0.0)
    def add_static_measurement(self, measurement: IMUMeasurement):
        self.acc_measurements.append(measurement.acceleration)
        self.gyro_measurements.append(measurement.angular_velocity)
        if len(self.acc_measurements) > self.window_size:
            self.acc_measurements.pop(0)
            self.gyro_measurements.pop(0)
        if len(self.acc_measurements) >= 10:
            self._update_bias_estimate(measurement.timestamp)
    def _update_bias_estimate(self, timestamp: float):
        acc_array = np.array(self.acc_measurements)
        gyro_array = np.array(self.gyro_measurements)
        new_gyro_bias = np.mean(gyro_array, axis=0)
        gravity_magnitude = 9.81
        acc_mean = np.mean(acc_array, axis=0)
        acc_magnitude = np.linalg.norm(acc_mean)
        if acc_magnitude > 0:
            gravity_direction = acc_mean / acc_magnitude
            expected_acc = gravity_direction * gravity_magnitude
            new_acc_bias = acc_mean - expected_acc
        else:
            new_acc_bias = acc_mean
        self.current_bias = IMUBias(new_acc_bias, new_gyro_bias, timestamp)
    def get_bias(self) -> IMUBias:
        return self.current_bias
    def is_converged(self) -> bool:
        if len(self.acc_measurements) < self.window_size:
            return False
        recent_acc = np.array(self.acc_measurements[-10:])
        recent_gyro = np.array(self.gyro_measurements[-10:])
        acc_std = np.std(recent_acc, axis=0)
        gyro_std = np.std(recent_gyro, axis=0)
        return np.all(acc_std < self.convergence_threshold) and np.all(gyro_std < self.convergence_threshold)
class UncertaintyPropagator:
    def __init__(self):
        self.process_noise = np.eye(15) * 1e-6
        self.measurement_noise = np.eye(6) * 1e-4
    def propagate_uncertainty(self, state: IMUState, measurements: List[IMUMeasurement], bias: IMUBias, dt: float) -> np.ndarray:
        F = self._compute_state_transition_matrix(state, measurements, dt)
        G = self._compute_noise_jacobian(state, dt)
        Q = self._compute_process_noise_matrix(dt)
        propagated_covariance = F @ state.covariance @ F.T + G @ Q @ G.T
        return propagated_covariance
    def _compute_state_transition_matrix(self, state: IMUState, measurements: List[IMUMeasurement], dt: float) -> np.ndarray:
        F = np.eye(15)
        if measurements:
            acc = measurements[-1].acceleration - state.accelerometer_bias
            gyro = measurements[-1].angular_velocity - state.gyroscope_bias
            R = state.orientation
            F[0:3, 3:6] = np.eye(3) * dt
            F[0:3, 6:9] = -R @ self._skew_symmetric(acc) * 0.5 * dt * dt
            F[0:3, 9:12] = -R * 0.5 * dt * dt
            F[3:6, 6:9] = -R @ self._skew_symmetric(acc) * dt
            F[3:6, 9:12] = -R * dt
            F[6:9, 6:9] = self._so3_exp(-gyro * dt)
            F[6:9, 12:15] = -np.eye(3) * dt
        return F
    def _compute_noise_jacobian(self, state: IMUState, dt: float) -> np.ndarray:
        G = np.zeros((15, 12))
        R = state.orientation
        G[0:3, 0:3] = -R * 0.5 * dt * dt
        G[3:6, 0:3] = -R * dt
        G[6:9, 3:6] = -np.eye(3) * dt
        G[9:12, 6:9] = np.eye(3) * dt
        G[12:15, 9:12] = np.eye(3) * dt
        return G
    def _compute_process_noise_matrix(self, dt: float) -> np.ndarray:
        Q = np.zeros((12, 12))
        Q[0:3, 0:3] = np.eye(3) * 0.01 * 0.01
        Q[3:6, 3:6] = np.eye(3) * 0.001 * 0.001
        Q[6:9, 6:9] = np.eye(3) * 0.0001 * 0.0001 * dt
        Q[9:12, 9:12] = np.eye(3) * 0.00001 * 0.00001 * dt
        return Q
    def _skew_symmetric(self, v: np.ndarray) -> np.ndarray:
        return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    def _so3_exp(self, omega: np.ndarray) -> np.ndarray:
        angle = np.linalg.norm(omega)
        if angle < 1e-8:
            return np.eye(3) + self._skew_symmetric(omega)
        axis = omega / angle
        K = self._skew_symmetric(axis)
        return np.eye(3) + np.sin(angle) * K + (1 - np.cos(angle)) * K @ K
class VisualInertialFusion:
    def __init__(self, camera_matrix: np.ndarray, imu_to_camera_transform: np.ndarray):
        self.camera_matrix = camera_matrix
        self.imu_to_camera_transform = imu_to_camera_transform
        self.camera_to_imu_transform = np.linalg.inv(imu_to_camera_transform)
        self.state_history = []
        self.keyframe_states = []
    def fuse_visual_imu_measurements(self, visual_pose: np.ndarray, visual_covariance: np.ndarray, imu_state: IMUState, measurement_noise: float = 0.1) -> IMUState:
        visual_pose_imu = self.camera_to_imu_transform @ visual_pose @ self.imu_to_camera_transform
        H = np.zeros((6, 15))
        H[0:3, 0:3] = np.eye(3)
        H[3:6, 6:9] = np.eye(3)
        R_measurement = np.eye(6) * measurement_noise * measurement_noise
        R_measurement[0:3, 0:3] += visual_covariance[0:3, 0:3]
        R_measurement[3:6, 3:6] += visual_covariance[3:6, 3:6]
        predicted_measurement = np.zeros(6)
        predicted_measurement[0:3] = imu_state.position
        predicted_measurement[3:6] = self._rotation_matrix_to_euler(imu_state.orientation)
        visual_measurement = np.zeros(6)
        visual_measurement[0:3] = visual_pose_imu[0:3, 3]
        visual_measurement[3:6] = self._rotation_matrix_to_euler(visual_pose_imu[0:3, 0:3])
        innovation = visual_measurement - predicted_measurement
        S = H @ imu_state.covariance @ H.T + R_measurement
        K = imu_state.covariance @ H.T @ np.linalg.inv(S)
        state_correction = K @ innovation
        corrected_position = imu_state.position + state_correction[0:3]
        corrected_velocity = imu_state.velocity + state_correction[3:6]
        rotation_correction = self._euler_to_rotation_matrix(state_correction[6:9])
        corrected_orientation = imu_state.orientation @ rotation_correction
        corrected_acc_bias = imu_state.accelerometer_bias + state_correction[9:12]
        corrected_gyro_bias = imu_state.gyroscope_bias + state_correction[12:15]
        corrected_covariance = (np.eye(15) - K @ H) @ imu_state.covariance
        return IMUState(timestamp=imu_state.timestamp, position=corrected_position, velocity=corrected_velocity, orientation=corrected_orientation, accelerometer_bias=corrected_acc_bias, gyroscope_bias=corrected_gyro_bias, covariance=corrected_covariance)
    def _rotation_matrix_to_euler(self, R: np.ndarray) -> np.ndarray:
        r = R.from_matrix(R)
        return r.as_euler('xyz')
    def _euler_to_rotation_matrix(self, euler: np.ndarray) -> np.ndarray:
        r = R.from_euler('xyz', euler)
        return r.as_matrix()
    def add_keyframe_state(self, state: IMUState):
        self.keyframe_states.append(state)
        if len(self.keyframe_states) > 10:
            self.keyframe_states.pop(0)
    def get_motion_model_prediction(self, dt: float, control_input: Optional[np.ndarray] = None) -> Dict:
        if not self.state_history:
            return {'position_change': np.zeros(3), 'velocity_change': np.zeros(3), 'orientation_change': np.eye(3)}
        current_state = self.state_history[-1]
        if len(self.state_history) > 1:
            prev_state = self.state_history[-2]
            dt_prev = current_state.timestamp - prev_state.timestamp
            if dt_prev > 0:
                velocity_estimate = (current_state.position - prev_state.position) / dt_prev
                acceleration_estimate = (current_state.velocity - prev_state.velocity) / dt_prev
            else:
                velocity_estimate = current_state.velocity
                acceleration_estimate = np.zeros(3)
        else:
            velocity_estimate = current_state.velocity
            acceleration_estimate = np.zeros(3)
        position_change = velocity_estimate * dt + 0.5 * acceleration_estimate * dt * dt
        velocity_change = acceleration_estimate * dt
        return {'position_change': position_change, 'velocity_change': velocity_change, 'orientation_change': np.eye(3), 'predicted_position': current_state.position + position_change, 'predicted_velocity': current_state.velocity + velocity_change}
class IMUCalibrator:
    def __init__(self):
        self.calibration_data = {'accelerometer': [], 'gyroscope': [], 'magnetometer': []}
        self.calibration_results = {}
    def collect_calibration_data(self, measurements: List[IMUMeasurement], sensor_type: str):
        if sensor_type == 'accelerometer':
            for measurement in measurements:
                self.calibration_data['accelerometer'].append(measurement.acceleration)
        elif sensor_type == 'gyroscope':
            for measurement in measurements:
                self.calibration_data['gyroscope'].append(measurement.angular_velocity)
    def calibrate_accelerometer(self) -> Dict:
        if len(self.calibration_data['accelerometer']) < 100:
            return {'success': False, 'error': 'Insufficient calibration data'}
        acc_data = np.array(self.calibration_data['accelerometer'])
        bias = np.mean(acc_data, axis=0)
        gravity_magnitude = 9.81
        acc_magnitude = np.linalg.norm(bias)
        if acc_magnitude > 0:
            gravity_direction = bias / acc_magnitude
            expected_gravity = gravity_direction * gravity_magnitude
            bias = bias - expected_gravity
        else:
            bias = np.zeros(3)
        scale_factors = np.std(acc_data, axis=0)
        scale_factors[scale_factors == 0] = 1.0
        self.calibration_results['accelerometer'] = {'bias': bias, 'scale_factors': scale_factors, 'noise_std': np.std(acc_data - np.mean(acc_data, axis=0), axis=0)}
        return {'success': True, 'bias': bias, 'scale_factors': scale_factors}
    def calibrate_gyroscope(self) -> Dict:
        if len(self.calibration_data['gyroscope']) < 100:
            return {'success': False, 'error': 'Insufficient calibration data'}
        gyro_data = np.array(self.calibration_data['gyroscope'])
        bias = np.mean(gyro_data, axis=0)
        scale_factors = np.std(gyro_data, axis=0)
        scale_factors[scale_factors == 0] = 1.0
        self.calibration_results['gyroscope'] = {'bias': bias, 'scale_factors': scale_factors, 'noise_std': np.std(gyro_data - bias, axis=0)}
        return {'success': True, 'bias': bias, 'scale_factors': scale_factors}
    def get_calibration_results(self) -> Dict:
        return self.calibration_results.copy()