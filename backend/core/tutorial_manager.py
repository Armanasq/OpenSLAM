import sys
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
from config.settings import BASE_DIR
import os

class TutorialProgress:
    def __init__(self, user_id: str, tutorial_id: str):
        self.user_id = user_id
        self.tutorial_id = tutorial_id
        self.current_step = 0
        self.completed_steps = []
        self.started_at = datetime.now()
        self.completed_at = None
        self.session_data = {}
        self.code_submissions = []
        self.hints_used = []

    def complete_step(self, step_index: int, code: str = "", execution_result: Dict = None):
        if step_index not in self.completed_steps:
            self.completed_steps.append(step_index)
            self.code_submissions.append({
                'step': step_index,
                'code': code,
                'result': execution_result,
                'timestamp': datetime.now()
            })

    def use_hint(self, step_index: int, hint_index: int):
        hint_usage = {
            'step': step_index,
            'hint': hint_index,
            'timestamp': datetime.now()
        }
        self.hints_used.append(hint_usage)

    def is_completed(self, total_steps: int) -> bool:
        return len(self.completed_steps) >= total_steps

    def get_completion_percentage(self, total_steps: int) -> float:
        return (len(self.completed_steps) / total_steps) * 100 if total_steps > 0 else 0

class TutorialContent:
    def __init__(self):
        self.tutorials = {}
        self._initialize_tutorials()

    def _initialize_tutorials(self):
        self.tutorials['feature_detection'] = {
            'id': 'feature_detection',
            'title': 'Feature Detection and Matching',
            'description': 'Master the fundamentals of feature detection and matching for visual SLAM applications',
            'difficulty': 'beginner',
            'estimated_time': 45,
            'prerequisites': [],
            'learning_objectives': [
                'Understand different feature detectors (ORB, SIFT, SURF)',
                'Learn feature matching techniques',
                'Implement robust feature matching with outlier rejection',
                'Visualize feature matches'
            ],
            'steps': [
                {
                    'id': 'fd_intro',
                    'title': 'Introduction to Features',
                    'content': 'Features are distinctive points in images that can be reliably detected and matched across different frames.',
                    'theory': 'A good feature should be: 1) Repeatable, 2) Distinctive, 3) Efficient',
                    'code_template': '''import cv2
import numpy as np

image_path = "/home/arman/project/SLAM/v1/data/00/image_0/000000.png"
image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

print(f"Image loaded: {image.shape}")
print(f"Image type: {image.dtype}")''',
                    'expected_output': 'Image loaded: (376, 1241)\nImage type: uint8',
                    'validation_criteria': ['Image successfully loaded', 'Correct image dimensions displayed'],
                    'hints': ['Check if the image path exists', 'Use cv2.IMREAD_GRAYSCALE for feature detection']
                }
            ]
        }

        self.tutorials['visual_odometry'] = {
            'id': 'visual_odometry',
            'title': 'Visual Odometry Implementation',
            'description': 'Build a complete visual odometry system from feature tracking to pose estimation',
            'difficulty': 'intermediate',
            'estimated_time': 90,
            'prerequisites': ['feature_detection'],
            'learning_objectives': [
                'Understand camera geometry and calibration',
                'Implement essential matrix estimation',
                'Recover camera pose from essential matrix',
                'Build a complete VO pipeline'
            ],
            'steps': [
                {
                    'id': 'vo_calibration',
                    'title': 'Camera Calibration Matrix',
                    'content': 'Camera calibration provides the intrinsic parameters needed to convert 2D image coordinates to 3D rays.',
                    'theory': 'The camera matrix K contains focal lengths (fx, fy) and principal point (cx, cy).',
                    'code_template': '''import numpy as np

P0 = np.array([718.856, 0, 607.1928, 0,
               0, 718.856, 185.2157, 0,
               0, 0, 1, 0]).reshape(3, 4)

K = P0[:3, :3]
print("Camera intrinsic matrix K:")
print(K)''',
                    'expected_output': 'Camera intrinsic matrix K:\n[[718.856   0.    607.1928]\n [  0.    718.856 185.2157]\n [  0.      0.      1.    ]]',
                    'validation_criteria': ['Correct K matrix extraction'],
                    'hints': ['K is the upper-left 3x3 part of P matrix']
                }
            ]
        }

    def get_tutorial(self, tutorial_id: str) -> Optional[Dict]:
        return self.tutorials.get(tutorial_id)

    def list_tutorials(self) -> List[Dict]:
        return [{
            'id': t['id'],
            'title': t['title'],
            'description': t['description'],
            'difficulty': t['difficulty'],
            'estimated_time': t['estimated_time'],
            'prerequisites': t['prerequisites'],
            'steps_count': len(t['steps'])
        } for t in self.tutorials.values()]

    def get_tutorial_step(self, tutorial_id: str, step_index: int) -> Optional[Dict]:
        tutorial = self.get_tutorial(tutorial_id)
        if tutorial and 0 <= step_index < len(tutorial['steps']):
            return tutorial['steps'][step_index]
        return None

class ProgressTracker:
    def __init__(self):
        self.progress_file = os.path.join(BASE_DIR, 'tutorial_progress.json')
        self.user_progress = {}
        self.load_progress()

    def load_progress(self):
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    for user_id, tutorials in data.items():
                        self.user_progress[user_id] = {}
                        for tutorial_id, progress_data in tutorials.items():
                            progress = TutorialProgress(user_id, tutorial_id)
                            progress.current_step = progress_data.get('current_step', 0)
                            progress.completed_steps = progress_data.get('completed_steps', [])
                            progress.started_at = datetime.fromisoformat(progress_data.get('started_at', datetime.now().isoformat()))
                            if progress_data.get('completed_at'):
                                progress.completed_at = datetime.fromisoformat(progress_data['completed_at'])
                            progress.session_data = progress_data.get('session_data', {})
                            progress.hints_used = progress_data.get('hints_used', [])
                            self.user_progress[user_id][tutorial_id] = progress
        except Exception as e:
            print(f"Error loading progress: {e}")
            self.user_progress = {}

    def save_progress(self):
        try:
            data = {}
            for user_id, tutorials in self.user_progress.items():
                data[user_id] = {}
                for tutorial_id, progress in tutorials.items():
                    data[user_id][tutorial_id] = {
                        'current_step': progress.current_step,
                        'completed_steps': progress.completed_steps,
                        'started_at': progress.started_at.isoformat(),
                        'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                        'session_data': progress.session_data,
                        'hints_used': progress.hints_used
                    }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving progress: {e}")

    def get_user_progress(self, user_id: str, tutorial_id: str) -> TutorialProgress:
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        if tutorial_id not in self.user_progress[user_id]:
            self.user_progress[user_id][tutorial_id] = TutorialProgress(user_id, tutorial_id)
        return self.user_progress[user_id][tutorial_id]

    def update_progress(self, user_id: str, tutorial_id: str, step_index: int, code: str = "", execution_result: Dict = None):
        progress = self.get_user_progress(user_id, tutorial_id)
        progress.complete_step(step_index, code, execution_result)
        progress.current_step = max(progress.current_step, step_index + 1)
        self.save_progress()

    def record_hint_usage(self, user_id: str, tutorial_id: str, step_index: int, hint_index: int):
        progress = self.get_user_progress(user_id, tutorial_id)
        progress.use_hint(step_index, hint_index)
        self.save_progress()

    def get_user_statistics(self, user_id: str) -> Dict:
        if user_id not in self.user_progress:
            return {
                'tutorials_started': 0,
                'tutorials_completed': 0,
                'total_steps_completed': 0,
                'total_time_spent': 0
            }

        tutorials = self.user_progress[user_id]
        completed_tutorials = sum(1 for p in tutorials.values() if p.completed_at is not None)
        total_steps = sum(len(p.completed_steps) for p in tutorials.values())
        
        total_time = 0
        for progress in tutorials.values():
            if progress.completed_at:
                total_time += (progress.completed_at - progress.started_at).total_seconds()
            else:
                total_time += (datetime.now() - progress.started_at).total_seconds()

        return {
            'tutorials_started': len(tutorials),
            'tutorials_completed': completed_tutorials,
            'total_steps_completed': total_steps,
            'total_time_spent': total_time / 3600
        }

class TutorialManager:
    def __init__(self):
        self.content = TutorialContent()
        self.progress_tracker = ProgressTracker()

    def get_tutorial_list(self, user_id: str) -> List[Dict]:
        tutorials = self.content.list_tutorials()
        for tutorial in tutorials:
            progress = self.progress_tracker.get_user_progress(user_id, tutorial['id'])
            tutorial['progress'] = {
                'current_step': progress.current_step,
                'completed_steps': len(progress.completed_steps),
                'total_steps': tutorial['steps_count'],
                'completion_percentage': progress.get_completion_percentage(tutorial['steps_count']),
                'is_completed': progress.is_completed(tutorial['steps_count'])
            }
        return tutorials

    def start_tutorial(self, user_id: str, tutorial_id: str) -> Dict:
        tutorial = self.content.get_tutorial(tutorial_id)
        if not tutorial:
            return {'success': False, 'error': 'Tutorial not found'}

        progress = self.progress_tracker.get_user_progress(user_id, tutorial_id)
        return {
            'success': True,
            'tutorial': tutorial,
            'progress': {
                'current_step': progress.current_step,
                'completed_steps': progress.completed_steps
            }
        }

    def get_tutorial_step(self, user_id: str, tutorial_id: str, step_index: int) -> Dict:
        step = self.content.get_tutorial_step(tutorial_id, step_index)
        if not step:
            return {'success': False, 'error': 'Step not found'}

        progress = self.progress_tracker.get_user_progress(user_id, tutorial_id)
        return {
            'success': True,
            'step': step,
            'is_completed': step_index in progress.completed_steps,
            'hints_used': [h for h in progress.hints_used if h['step'] == step_index]
        }

    def submit_step_solution(self, user_id: str, tutorial_id: str, step_index: int, code: str, execution_result: Dict) -> Dict:
        step = self.content.get_tutorial_step(tutorial_id, step_index)
        if not step:
            return {'success': False, 'error': 'Step not found'}

        is_correct = self._validate_solution(step, code, execution_result)
        if is_correct:
            self.progress_tracker.update_progress(user_id, tutorial_id, step_index, code, execution_result)

        return {
            'success': True,
            'is_correct': is_correct,
            'feedback': self._generate_feedback(step, code, execution_result, is_correct)
        }

    def _validate_solution(self, step: Dict, code: str, execution_result: Dict) -> bool:
        if not execution_result.get('success', False):
            return False

        expected_output = step.get('expected_output', '').strip()
        actual_output = execution_result.get('output', '').strip()
        
        return expected_output in actual_output or actual_output in expected_output

    def _generate_feedback(self, step: Dict, code: str, execution_result: Dict, is_correct: bool) -> str:
        if is_correct:
            return "Excellent! Your solution is correct. You can proceed to the next step."
        elif not execution_result.get('success', False):
            return f"There's an error in your code: {execution_result.get('error', 'Unknown error')}"
        else:
            return "Your code runs but doesn't produce the expected output. Check the expected output and try again."

    def use_hint(self, user_id: str, tutorial_id: str, step_index: int, hint_index: int) -> Dict:
        step = self.content.get_tutorial_step(tutorial_id, step_index)
        if not step or hint_index >= len(step.get('hints', [])):
            return {'success': False, 'error': 'Hint not found'}

        self.progress_tracker.record_hint_usage(user_id, tutorial_id, step_index, hint_index)
        return {
            'success': True,
            'hint': step['hints'][hint_index]
        }

    def get_user_statistics(self, user_id: str) -> Dict:
        return self.progress_tracker.get_user_statistics(user_id)