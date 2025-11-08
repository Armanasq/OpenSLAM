import sys
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import cv2
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from backend.algorithms.slam_backend import Landmark, KeyFrame
@dataclass
class MapPoint:
    id: int
    position: np.ndarray
    color: np.ndarray
    normal: np.ndarray
    descriptor: Optional[np.ndarray]
    observations: List[Tuple[int, np.ndarray]]
    creation_frame: int
    last_seen_frame: int
    times_observed: int
    times_visible: int
@dataclass
class OccupancyCell:
    x: int
    y: int
    probability: float
    height: float
    color: np.ndarray
class Map3D:
    def __init__(self, max_points: int = 100000):
        self.map_points = {}
        self.keyframes = {}
        self.max_points = max_points
        self.next_point_id = 0
        self.bounding_box = {'min': np.array([float('inf')] * 3), 'max': np.array([float('-inf')] * 3)}
    def add_map_point(self, position: np.ndarray, color: np.ndarray = None, normal: np.ndarray = None, descriptor: np.ndarray = None, creation_frame: int = 0) -> int:
        if len(self.map_points) >= self.max_points:
            self._remove_oldest_points(self.max_points // 10)
        point_id = self.next_point_id
        self.next_point_id += 1
        if color is None:
            color = np.array([128, 128, 128])
        if normal is None:
            normal = np.array([0, 0, 1])
        map_point = MapPoint(id=point_id, position=position.copy(), color=color, normal=normal, descriptor=descriptor, observations=[], creation_frame=creation_frame, last_seen_frame=creation_frame, times_observed=1, times_visible=1)
        self.map_points[point_id] = map_point
        self._update_bounding_box(position)
        return point_id
    def add_observation(self, point_id: int, keyframe_id: int, observation: np.ndarray):
        if point_id in self.map_points:
            self.map_points[point_id].observations.append((keyframe_id, observation))
            self.map_points[point_id].last_seen_frame = keyframe_id
            self.map_points[point_id].times_observed += 1
    def update_point_position(self, point_id: int, new_position: np.ndarray):
        if point_id in self.map_points:
            self.map_points[point_id].position = new_position.copy()
            self._update_bounding_box(new_position)
    def remove_point(self, point_id: int):
        if point_id in self.map_points:
            del self.map_points[point_id]
    def get_points_in_region(self, center: np.ndarray, radius: float) -> List[MapPoint]:
        points_in_region = []
        for point in self.map_points.values():
            distance = np.linalg.norm(point.position - center)
            if distance <= radius:
                points_in_region.append(point)
        return points_in_region
    def get_visible_points(self, camera_pose: np.ndarray, camera_matrix: np.ndarray, image_size: Tuple[int, int], max_distance: float = 100.0) -> List[MapPoint]:
        visible_points = []
        camera_position = camera_pose[:3, 3]
        camera_rotation = camera_pose[:3, :3]
        for point in self.map_points.values():
            point_camera = camera_rotation.T @ (point.position - camera_position)
            if point_camera[2] > 0 and point_camera[2] < max_distance:
                projected = camera_matrix @ point_camera
                u, v = projected[0] / projected[2], projected[1] / projected[2]
                if 0 <= u < image_size[0] and 0 <= v < image_size[1]:
                    visible_points.append(point)
        return visible_points
    def _update_bounding_box(self, position: np.ndarray):
        self.bounding_box['min'] = np.minimum(self.bounding_box['min'], position)
        self.bounding_box['max'] = np.maximum(self.bounding_box['max'], position)
    def _remove_oldest_points(self, num_to_remove: int):
        points_by_age = sorted(self.map_points.values(), key=lambda p: p.creation_frame)
        for i in range(min(num_to_remove, len(points_by_age))):
            self.remove_point(points_by_age[i].id)
    def get_map_statistics(self) -> Dict:
        if not self.map_points:
            return {'num_points': 0, 'bounding_box_size': np.zeros(3), 'average_observations': 0.0}
        total_observations = sum(point.times_observed for point in self.map_points.values())
        avg_observations = total_observations / len(self.map_points)
        bbox_size = self.bounding_box['max'] - self.bounding_box['min']
        return {'num_points': len(self.map_points), 'bounding_box_size': bbox_size, 'bounding_box_min': self.bounding_box['min'], 'bounding_box_max': self.bounding_box['max'], 'average_observations': avg_observations}
    def export_point_cloud(self, format: str = 'ply') -> str:
        if format == 'ply':
            return self._export_ply()
        elif format == 'pcd':
            return self._export_pcd()
        else:
            raise ValueError(f"Unsupported format: {format}")
    def _export_ply(self) -> str:
        header = f"""ply
format ascii 1.0
element vertex {len(self.map_points)}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""
        points_data = []
        for point in self.map_points.values():
            x, y, z = point.position
            r, g, b = point.color.astype(int)
            points_data.append(f"{x} {y} {z} {r} {g} {b}")
        return header + '\n'.join(points_data)
    def _export_pcd(self) -> str:
        header = f"""# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z rgb
SIZE 4 4 4 4
TYPE F F F U
COUNT 1 1 1 1
WIDTH {len(self.map_points)}
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS {len(self.map_points)}
DATA ascii
"""
        points_data = []
        for point in self.map_points.values():
            x, y, z = point.position
            r, g, b = point.color.astype(int)
            rgb = (r << 16) | (g << 8) | b
            points_data.append(f"{x} {y} {z} {rgb}")
        return header + '\n'.join(points_data)
class OccupancyGrid:
    def __init__(self, resolution: float = 0.1, width: int = 1000, height: int = 1000, origin: np.ndarray = None):
        self.resolution = resolution
        self.width = width
        self.height = height
        self.origin = origin if origin is not None else np.array([0.0, 0.0])
        self.grid = np.full((height, width), 0.5, dtype=np.float32)
        self.height_map = np.zeros((height, width), dtype=np.float32)
        self.color_map = np.zeros((height, width, 3), dtype=np.uint8)
        self.update_count = np.zeros((height, width), dtype=np.int32)
    def world_to_grid(self, world_pos: np.ndarray) -> Tuple[int, int]:
        grid_x = int((world_pos[0] - self.origin[0]) / self.resolution)
        grid_y = int((world_pos[1] - self.origin[1]) / self.resolution)
        return grid_x, grid_y
    def grid_to_world(self, grid_x: int, grid_y: int) -> np.ndarray:
        world_x = grid_x * self.resolution + self.origin[0]
        world_y = grid_y * self.resolution + self.origin[1]
        return np.array([world_x, world_y])
    def is_valid_cell(self, grid_x: int, grid_y: int) -> bool:
        return 0 <= grid_x < self.width and 0 <= grid_y < self.height
    def update_cell(self, world_pos: np.ndarray, probability: float, height: float = 0.0, color: np.ndarray = None):
        grid_x, grid_y = self.world_to_grid(world_pos)
        if self.is_valid_cell(grid_x, grid_y):
            current_prob = self.grid[grid_y, grid_x]
            log_odds_current = np.log(current_prob / (1 - current_prob + 1e-8))
            log_odds_update = np.log(probability / (1 - probability + 1e-8))
            log_odds_new = log_odds_current + log_odds_update
            new_prob = 1 / (1 + np.exp(-log_odds_new))
            self.grid[grid_y, grid_x] = np.clip(new_prob, 0.01, 0.99)
            self.height_map[grid_y, grid_x] = (self.height_map[grid_y, grid_x] * self.update_count[grid_y, grid_x] + height) / (self.update_count[grid_y, grid_x] + 1)
            if color is not None:
                self.color_map[grid_y, grid_x] = color
            self.update_count[grid_y, grid_x] += 1
    def raycast_update(self, start_pos: np.ndarray, end_pos: np.ndarray, hit: bool = True):
        start_grid = self.world_to_grid(start_pos)
        end_grid = self.world_to_grid(end_pos)
        ray_cells = self._bresenham_line(start_grid[0], start_grid[1], end_grid[0], end_grid[1])
        for i, (x, y) in enumerate(ray_cells):
            if self.is_valid_cell(x, y):
                if i == len(ray_cells) - 1 and hit:
                    self.update_cell(self.grid_to_world(x, y), 0.9)
                else:
                    self.update_cell(self.grid_to_world(x, y), 0.1)
    def _bresenham_line(self, x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            points.append((x, y))
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        return points
    def get_occupancy_image(self) -> np.ndarray:
        occupancy_image = (self.grid * 255).astype(np.uint8)
        return cv2.applyColorMap(255 - occupancy_image, cv2.COLORMAP_GRAY)
    def get_height_image(self) -> np.ndarray:
        height_normalized = (self.height_map - self.height_map.min()) / (self.height_map.max() - self.height_map.min() + 1e-8)
        height_image = (height_normalized * 255).astype(np.uint8)
        return cv2.applyColorMap(height_image, cv2.COLORMAP_JET)
    def export_map(self, filename: str, format: str = 'pgm'):
        if format == 'pgm':
            occupancy_image = (self.grid * 255).astype(np.uint8)
            cv2.imwrite(filename, 255 - occupancy_image)
        elif format == 'png':
            occupancy_image = self.get_occupancy_image()
            cv2.imwrite(filename, occupancy_image)
class MapBuilder:
    def __init__(self, camera_matrix: np.ndarray, use_occupancy_grid: bool = True, grid_resolution: float = 0.1):
        self.camera_matrix = camera_matrix
        self.map_3d = Map3D()
        self.use_occupancy_grid = use_occupancy_grid
        if use_occupancy_grid:
            self.occupancy_grid = OccupancyGrid(resolution=grid_resolution)
        else:
            self.occupancy_grid = None
        self.keyframe_poses = {}
    def add_keyframe_observations(self, keyframe_id: int, pose: np.ndarray, keypoints: List, descriptors: np.ndarray, depth_map: Optional[np.ndarray] = None, image: Optional[np.ndarray] = None):
        self.keyframe_poses[keyframe_id] = pose
        if depth_map is not None and image is not None:
            self._add_dense_points(keyframe_id, pose, depth_map, image)
        else:
            self._add_sparse_points(keyframe_id, pose, keypoints, descriptors)
        if self.use_occupancy_grid:
            self._update_occupancy_grid(pose, depth_map, image)
    def _add_sparse_points(self, keyframe_id: int, pose: np.ndarray, keypoints: List, descriptors: np.ndarray):
        camera_position = pose[:3, 3]
        camera_rotation = pose[:3, :3]
        for i, keypoint in enumerate(keypoints):
            depth = 5.0
            u, v = keypoint.pt
            ray_direction = np.linalg.inv(self.camera_matrix) @ np.array([u, v, 1])
            ray_direction = ray_direction / np.linalg.norm(ray_direction)
            world_ray_direction = camera_rotation @ ray_direction
            world_position = camera_position + world_ray_direction * depth
            color = np.array([128, 128, 128])
            descriptor = descriptors[i] if descriptors is not None and i < len(descriptors) else None
            point_id = self.map_3d.add_map_point(world_position, color, descriptor=descriptor, creation_frame=keyframe_id)
            observation = np.array([u, v])
            self.map_3d.add_observation(point_id, keyframe_id, observation)
    def _add_dense_points(self, keyframe_id: int, pose: np.ndarray, depth_map: np.ndarray, image: np.ndarray):
        camera_position = pose[:3, 3]
        camera_rotation = pose[:3, :3]
        height, width = depth_map.shape
        fx, fy = self.camera_matrix[0, 0], self.camera_matrix[1, 1]
        cx, cy = self.camera_matrix[0, 2], self.camera_matrix[1, 2]
        step = 5
        for v in range(0, height, step):
            for u in range(0, width, step):
                depth = depth_map[v, u]
                if depth > 0 and depth < 50:
                    x_cam = (u - cx) * depth / fx
                    y_cam = (v - cy) * depth / fy
                    z_cam = depth
                    point_camera = np.array([x_cam, y_cam, z_cam])
                    world_position = camera_position + camera_rotation @ point_camera
                    if len(image.shape) == 3:
                        color = image[v, u]
                    else:
                        gray_val = image[v, u]
                        color = np.array([gray_val, gray_val, gray_val])
                    point_id = self.map_3d.add_map_point(world_position, color, creation_frame=keyframe_id)
                    observation = np.array([u, v])
                    self.map_3d.add_observation(point_id, keyframe_id, observation)
    def _update_occupancy_grid(self, pose: np.ndarray, depth_map: Optional[np.ndarray], image: Optional[np.ndarray]):
        if not self.use_occupancy_grid or depth_map is None:
            return
        camera_position = pose[:3, 3]
        camera_rotation = pose[:3, :3]
        height, width = depth_map.shape
        fx, fy = self.camera_matrix[0, 0], self.camera_matrix[1, 1]
        cx, cy = self.camera_matrix[0, 2], self.camera_matrix[1, 2]
        step = 10
        for v in range(0, height, step):
            for u in range(0, width, step):
                depth = depth_map[v, u]
                if depth > 0:
                    x_cam = (u - cx) * depth / fx
                    y_cam = (v - cy) * depth / fy
                    z_cam = depth
                    point_camera = np.array([x_cam, y_cam, z_cam])
                    world_position = camera_position + camera_rotation @ point_camera
                    self.occupancy_grid.raycast_update(camera_position[:2], world_position[:2], hit=True)
    def triangulate_stereo_points(self, keyframe1_id: int, keyframe2_id: int, matches: List[Tuple[int, int]], keypoints1: List, keypoints2: List):
        if keyframe1_id not in self.keyframe_poses or keyframe2_id not in self.keyframe_poses:
            return
        pose1 = self.keyframe_poses[keyframe1_id]
        pose2 = self.keyframe_poses[keyframe2_id]
        P1 = self.camera_matrix @ np.hstack([np.eye(3), np.zeros((3, 1))])
        relative_pose = np.linalg.inv(pose1) @ pose2
        P2 = self.camera_matrix @ np.hstack([relative_pose[:3, :3], relative_pose[:3, 3:4]])
        for match_idx1, match_idx2 in matches:
            if match_idx1 < len(keypoints1) and match_idx2 < len(keypoints2):
                pt1 = np.array(keypoints1[match_idx1].pt)
                pt2 = np.array(keypoints2[match_idx2].pt)
                point_4d = cv2.triangulatePoints(P1, P2, pt1.reshape(2, 1), pt2.reshape(2, 1))
                point_3d = point_4d[:3] / point_4d[3]
                world_position = pose1[:3, :3] @ point_3d.flatten() + pose1[:3, 3]
                if point_3d[2] > 0 and point_3d[2] < 100:
                    color = np.array([0, 255, 0])
                    point_id = self.map_3d.add_map_point(world_position, color, creation_frame=keyframe1_id)
                    self.map_3d.add_observation(point_id, keyframe1_id, pt1)
                    self.map_3d.add_observation(point_id, keyframe2_id, pt2)
    def get_map_visualization_data(self) -> Dict:
        points = []
        colors = []
        for point in self.map_3d.map_points.values():
            points.append(point.position.tolist())
            colors.append(point.color.tolist())
        trajectory = []
        for kf_id in sorted(self.keyframe_poses.keys()):
            pose = self.keyframe_poses[kf_id]
            trajectory.append(pose[:3, 3].tolist())
        result = {'points': points, 'colors': colors, 'trajectory': trajectory, 'map_statistics': self.map_3d.get_map_statistics()}
        if self.use_occupancy_grid:
            result['occupancy_grid'] = {'grid': self.occupancy_grid.grid.tolist(), 'resolution': self.occupancy_grid.resolution, 'origin': self.occupancy_grid.origin.tolist(), 'width': self.occupancy_grid.width, 'height': self.occupancy_grid.height}
        return result
    def optimize_map(self, max_points: Optional[int] = None):
        if max_points and len(self.map_3d.map_points) > max_points:
            points_by_quality = sorted(self.map_3d.map_points.values(), key=lambda p: p.times_observed, reverse=True)
            points_to_keep = points_by_quality[:max_points]
            points_to_remove = [p.id for p in self.map_3d.map_points.values() if p not in points_to_keep]
            for point_id in points_to_remove:
                self.map_3d.remove_point(point_id)
    def export_map(self, filename: str, format: str = 'ply'):
        if format in ['ply', 'pcd']:
            map_data = self.map_3d.export_point_cloud(format)
            with open(filename, 'w') as f:
                f.write(map_data)
        elif format == 'occupancy' and self.use_occupancy_grid:
            self.occupancy_grid.export_map(filename, 'pgm')
    def reset(self):
        self.map_3d = Map3D()
        if self.use_occupancy_grid:
            self.occupancy_grid = OccupancyGrid()
        self.keyframe_poses = {}