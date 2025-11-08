import sys
import os
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from backend.core.dataset_manager import DatasetManager, ValidationError
from backend.core.data_stream import DataStream, DataPreprocessor
from config.settings import KITTI_DATASET_PATH
def test_kitti_validation():
    manager = DatasetManager()
    dataset_path = KITTI_DATASET_PATH
    is_valid, errors = manager.validate_kitti_format(dataset_path)
    print(f"Dataset validation: {is_valid}")
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    return is_valid
def test_dataset_loading():
    manager = DatasetManager()
    dataset_path = KITTI_DATASET_PATH
    try:
        dataset = manager.load_kitti_dataset(dataset_path)
        print(f"Dataset loaded: {dataset.name}")
        print(f"Sequence length: {dataset.sequence_length}")
        print(f"Available sensors: {dataset.sensors}")
        print(f"Has ground truth: {dataset.metadata.get('has_ground_truth', False)}")
        return dataset
    except ValidationError as e:
        print(f"Validation failed: {e.message}")
        for error in e.errors:
            print(f"  - {error}")
        return None
def test_frame_loading():
    manager = DatasetManager()
    dataset_path = KITTI_DATASET_PATH
    try:
        dataset = manager.load_kitti_dataset(dataset_path)
        frame_data = manager.load_frame_data(dataset.id, 0)
        if frame_data:
            print("Frame 0 data:")
            for key, value in frame_data.items():
                print(f"  {key}: {value}")
        return frame_data
    except Exception as e:
        print(f"Frame loading failed: {e}")
        return None
def test_data_stream():
    manager = DatasetManager()
    dataset_path = KITTI_DATASET_PATH
    try:
        dataset = manager.load_kitti_dataset(dataset_path)
        stream = DataStream(manager, dataset.id, (0, 5))
        print(f"Stream frame count: {stream.get_frame_count()}")
        frame_count = 0
        while True:
            import asyncio
            frame = asyncio.run(stream.next_frame())
            if frame is None:
                break
            frame_count += 1
            print(f"Streamed frame {frame['frame_id']}")
        print(f"Total frames streamed: {frame_count}")
        return True
    except Exception as e:
        print(f"Data stream test failed: {e}")
        return False
def test_preprocessing():
    manager = DatasetManager()
    dataset_path = KITTI_DATASET_PATH
    try:
        dataset = manager.load_kitti_dataset(dataset_path)
        preprocessor = DataPreprocessor(manager)
        transforms = preprocessor.align_coordinate_systems(dataset.id)
        print("Coordinate system transforms:")
        for key, value in transforms.items():
            print(f"  {key}: {type(value)}")
        intrinsics = preprocessor.extract_camera_intrinsics(dataset.id)
        print("Camera intrinsics:")
        for key, matrix in intrinsics.items():
            print(f"  {key}: {matrix.shape}")
        return True
    except Exception as e:
        print(f"Preprocessing test failed: {e}")
        return False
if __name__ == "__main__":
    print("Testing KITTI dataset validation...")
    test_kitti_validation()
    print("\nTesting dataset loading...")
    test_dataset_loading()
    print("\nTesting frame loading...")
    test_frame_loading()
    print("\nTesting data stream...")
    test_data_stream()
    print("\nTesting preprocessing...")
    test_preprocessing()
    print("\nAll tests completed.")