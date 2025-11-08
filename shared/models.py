from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
class Dataset(BaseModel):
    id: str
    name: str
    format: str
    sequence_length: int
    sensors: List[str]
    calibration: Dict
    metadata: Dict
    created_at: datetime
    file_paths: Dict[str, str]
class Algorithm(BaseModel):
    id: str
    name: str
    type: str
    source_code: str
    interface_version: str
    performance_metrics: Dict
    created_at: datetime
    updated_at: datetime
class Execution(BaseModel):
    id: str
    algorithm_id: str
    dataset_id: str
    frame_range: Tuple[int, int]
    status: str
    results: Dict
    metrics: Dict
    started_at: datetime
    completed_at: Optional[datetime]
class TrajectoryPoint(BaseModel):
    position: Tuple[float, float, float]
    orientation: Tuple[float, float, float, float]
    timestamp: float
    frame_id: int
class PerformanceMetrics(BaseModel):
    ate: float
    rpe_trans: float
    rpe_rot: float
    execution_time: float
    memory_usage: float