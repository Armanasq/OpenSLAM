import sys
import threading
import time
import psutil
import os
from typing import Dict, List, Optional, Any, Callable
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
class Breakpoint:
    def __init__(self, line_number: int, condition: str = "", enabled: bool = True):
        self.line_number = line_number
        self.condition = condition
        self.enabled = enabled
        self.hit_count = 0
class DebugFrame:
    def __init__(self, frame_id: str, function_name: str, line_number: int, variables: Dict):
        self.frame_id = frame_id
        self.function_name = function_name
        self.line_number = line_number
        self.variables = variables
        self.timestamp = time.time()
class ExecutionMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.start_time = 0.0
        self.cpu_usage = []
        self.memory_usage = []
        self.execution_steps = []
        self.current_line = 0
        self.total_lines = 0
        self.process = psutil.Process(os.getpid())
    def start_monitoring(self, total_lines: int = 0):
        self.is_monitoring = True
        self.start_time = time.time()
        self.total_lines = total_lines
        self.current_line = 0
        self.cpu_usage = []
        self.memory_usage = []
        self.execution_steps = []
        self._monitor_thread = threading.Thread(target=self._monitor_resources)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    def stop_monitoring(self):
        self.is_monitoring = False
        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=1.0)
    def _monitor_resources(self):
        while self.is_monitoring:
            try:
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.cpu_usage.append({'timestamp': time.time() - self.start_time, 'cpu_percent': cpu_percent})
                self.memory_usage.append({'timestamp': time.time() - self.start_time, 'memory_mb': memory_mb})
                time.sleep(0.1)
            except:
                break
    def update_progress(self, current_line: int, function_name: str = "", variables: Dict = None):
        self.current_line = current_line
        step = {'line': current_line, 'function': function_name, 'timestamp': time.time() - self.start_time, 'variables': variables or {}}
        self.execution_steps.append(step)
    def get_progress(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return min(1.0, self.current_line / self.total_lines)
    def get_execution_time(self) -> float:
        return time.time() - self.start_time
    def get_resource_usage(self) -> Dict:
        return {'cpu_usage': self.cpu_usage.copy(), 'memory_usage': self.memory_usage.copy(), 'execution_steps': self.execution_steps.copy()}
class ResourceManager:
    def __init__(self, max_memory_mb: float = 512.0, max_cpu_time: float = 30.0):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time = max_cpu_time
        self.process = psutil.Process(os.getpid())
        self.start_time = 0.0
        self.is_monitoring = False
    def start_monitoring(self):
        self.start_time = time.time()
        self.is_monitoring = True
    def check_limits(self) -> Tuple[bool, str]:
        if not self.is_monitoring:
            return True, ""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            if memory_mb > self.max_memory_mb:
                return False, f"Memory limit exceeded: {memory_mb:.1f}MB > {self.max_memory_mb}MB"
            execution_time = time.time() - self.start_time
            if execution_time > self.max_cpu_time:
                return False, f"Execution time limit exceeded: {execution_time:.1f}s > {self.max_cpu_time}s"
            return True, ""
        except:
            return True, ""
    def stop_monitoring(self):
        self.is_monitoring = False
class Debugger:
    def __init__(self):
        self.breakpoints = {}
        self.call_stack = []
        self.variables_history = []
        self.is_debugging = False
        self.current_frame = None
        self.step_mode = False
        self.monitor = ExecutionMonitor()
        self.resource_manager = ResourceManager()
    def add_breakpoint(self, line_number: int, condition: str = "") -> bool:
        self.breakpoints[line_number] = Breakpoint(line_number, condition, True)
        return True
    def remove_breakpoint(self, line_number: int) -> bool:
        if line_number in self.breakpoints:
            del self.breakpoints[line_number]
            return True
        return False
    def toggle_breakpoint(self, line_number: int) -> bool:
        if line_number in self.breakpoints:
            self.breakpoints[line_number].enabled = not self.breakpoints[line_number].enabled
            return self.breakpoints[line_number].enabled
        return False
    def list_breakpoints(self) -> List[Dict]:
        result = []
        for bp in self.breakpoints.values():
            result.append({'line_number': bp.line_number, 'condition': bp.condition, 'enabled': bp.enabled, 'hit_count': bp.hit_count})
        return result
    def clear_breakpoints(self):
        self.breakpoints = {}
    def should_break(self, line_number: int, local_vars: Dict) -> bool:
        if line_number not in self.breakpoints:
            return False
        bp = self.breakpoints[line_number]
        if not bp.enabled:
            return False
        if bp.condition:
            try:
                result = eval(bp.condition, {}, local_vars)
                if not result:
                    return False
            except:
                return False
        bp.hit_count += 1
        return True
    def inspect_variable(self, variable_name: str, frame_vars: Dict) -> Optional[Dict]:
        if variable_name not in frame_vars:
            return None
        value = frame_vars[variable_name]
        return {'name': variable_name, 'type': type(value).__name__, 'value': str(value), 'size': sys.getsizeof(value) if hasattr(sys, 'getsizeof') else 0}
    def get_call_stack(self) -> List[DebugFrame]:
        return self.call_stack.copy()
    def push_frame(self, function_name: str, line_number: int, variables: Dict):
        frame_id = f"{function_name}_{len(self.call_stack)}"
        frame = DebugFrame(frame_id, function_name, line_number, variables.copy())
        self.call_stack.append(frame)
        self.current_frame = frame
    def pop_frame(self):
        if self.call_stack:
            self.call_stack.pop()
            self.current_frame = self.call_stack[-1] if self.call_stack else None
    def start_debugging(self, total_lines: int = 0):
        self.is_debugging = True
        self.monitor.start_monitoring(total_lines)
        self.resource_manager.start_monitoring()
    def stop_debugging(self):
        self.is_debugging = False
        self.monitor.stop_monitoring()
        self.resource_manager.stop_monitoring()
        self.call_stack = []
        self.current_frame = None
    def step_over(self):
        self.step_mode = True
    def continue_execution(self):
        self.step_mode = False
    def get_debug_info(self) -> Dict:
        return {'breakpoints': self.list_breakpoints(), 'call_stack': [{'function': f.function_name, 'line': f.line_number, 'variables': f.variables} for f in self.call_stack], 'current_frame': {'function': self.current_frame.function_name, 'line': self.current_frame.line_number, 'variables': self.current_frame.variables} if self.current_frame else None, 'progress': self.monitor.get_progress(), 'execution_time': self.monitor.get_execution_time(), 'resource_usage': self.monitor.get_resource_usage()}
class DebuggerCodeExecutor:
    def __init__(self):
        self.debugger = Debugger()
        self.code_lines = []
        self.current_line_index = 0
    def execute_with_debugging(self, code: str) -> Dict:
        self.code_lines = code.split('\n')
        self.current_line_index = 0
        self.debugger.start_debugging(len(self.code_lines))
        try:
            namespace = {'__builtins__': __builtins__}
            for i, line in enumerate(self.code_lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                self.current_line_index = i + 1
                self.debugger.monitor.update_progress(self.current_line_index, "main", namespace)
                within_limits, limit_error = self.debugger.resource_manager.check_limits()
                if not within_limits:
                    return {'success': False, 'error': limit_error, 'debug_info': self.debugger.get_debug_info()}
                if self.debugger.should_break(self.current_line_index, namespace) or self.debugger.step_mode:
                    debug_info = self.debugger.get_debug_info()
                    debug_info['paused_at_line'] = self.current_line_index
                    debug_info['current_line'] = line
                    return {'success': True, 'paused': True, 'debug_info': debug_info, 'namespace': namespace}
                try:
                    exec(line, namespace)
                except Exception as e:
                    return {'success': False, 'error': f"Line {self.current_line_index}: {str(e)}", 'debug_info': self.debugger.get_debug_info()}
            return {'success': True, 'paused': False, 'debug_info': self.debugger.get_debug_info(), 'namespace': namespace}
        finally:
            self.debugger.stop_debugging()