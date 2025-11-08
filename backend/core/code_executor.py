import sys
import ast
import traceback
import io
import contextlib
from typing import Dict, List, Optional, Any, Tuple
sys.path.append('/home/arman/project/SLAM/v1/OpenSLAM_v0.1')
class SyntaxError(Exception):
    def __init__(self, message: str, line_number: int, column: int, suggestion: str = ""):
        self.message = message
        self.line_number = line_number
        self.column = column
        self.suggestion = suggestion
        super().__init__(message)
class ExecutionResult:
    def __init__(self, success: bool, output: str = "", error: str = "", variables: Dict = None, execution_time: float = 0.0):
        self.success = success
        self.output = output
        self.error = error
        self.variables = variables or {}
        self.execution_time = execution_time
class CodeExecutor:
    def __init__(self):
        self.global_namespace = {'__builtins__': __builtins__, 'np': __import__('numpy'), 'cv2': None}
        self.execution_history = []
        self.output_buffer = io.StringIO()
        self._setup_cv2()
    def _setup_cv2(self):
        try:
            import cv2
            self.global_namespace['cv2'] = cv2
        except ImportError:
            pass
    def validate_syntax(self, code: str) -> Tuple[bool, List[SyntaxError]]:
        errors = []
        try:
            ast.parse(code)
            return True, []
        except SyntaxError as e:
            suggestion = self._generate_suggestion(e)
            syntax_error = SyntaxError(str(e.msg), e.lineno or 0, e.offset or 0, suggestion)
            errors.append(syntax_error)
            return False, errors
        except Exception as e:
            syntax_error = SyntaxError(str(e), 0, 0, "Check code structure")
            errors.append(syntax_error)
            return False, errors
    def _generate_suggestion(self, syntax_error) -> str:
        error_msg = str(syntax_error.msg).lower()
        if "invalid syntax" in error_msg:
            return "Check for missing colons, parentheses, or indentation"
        elif "unexpected eof" in error_msg:
            return "Check for unclosed parentheses, brackets, or quotes"
        elif "indentation" in error_msg:
            return "Fix indentation - use consistent spaces or tabs"
        elif "name" in error_msg and "not defined" in error_msg:
            return "Check variable names and imports"
        else:
            return "Review syntax near the error location"
    def execute_code(self, code: str, timeout: float = 30.0) -> ExecutionResult:
        import time
        start_time = time.time()
        is_valid, syntax_errors = self.validate_syntax(code)
        if not is_valid:
            error_msg = "\n".join([f"Line {err.line_number}: {err.message} - {err.suggestion}" for err in syntax_errors])
            return ExecutionResult(False, "", error_msg, {}, 0.0)
        self.output_buffer = io.StringIO()
        local_namespace = {}
        try:
            with contextlib.redirect_stdout(self.output_buffer), contextlib.redirect_stderr(self.output_buffer):
                exec(code, self.global_namespace, local_namespace)
            execution_time = time.time() - start_time
            output = self.output_buffer.getvalue()
            self.global_namespace.update(local_namespace)
            result = ExecutionResult(True, output, "", local_namespace, execution_time)
            self.execution_history.append({'code': code, 'result': result, 'timestamp': time.time()})
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return ExecutionResult(False, self.output_buffer.getvalue(), error_msg, {}, execution_time)
    def get_variable(self, name: str) -> Any:
        return self.global_namespace.get(name)
    def set_variable(self, name: str, value: Any) -> None:
        self.global_namespace[name] = value
    def list_variables(self) -> Dict[str, str]:
        variables = {}
        for name, value in self.global_namespace.items():
            if not name.startswith('__') and name not in ['np', 'cv2']:
                try:
                    variables[name] = str(type(value).__name__)
                except:
                    variables[name] = "unknown"
        return variables
    def clear_variables(self) -> None:
        keep_vars = {'__builtins__', 'np', 'cv2'}
        self.global_namespace = {k: v for k, v in self.global_namespace.items() if k in keep_vars}
    def get_execution_history(self) -> List[Dict]:
        return self.execution_history.copy()
    def clear_history(self) -> None:
        self.execution_history = []
class SyntaxHighlighter:
    def __init__(self):
        self.keywords = {'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'import', 'from', 'return', 'yield', 'break', 'continue', 'pass', 'lambda', 'with', 'as', 'raise', 'assert', 'del', 'global', 'nonlocal', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None'}
        self.builtin_functions = {'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter', 'sum', 'max', 'min', 'abs', 'round', 'sorted', 'reversed', 'any', 'all', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr', 'dir', 'help'}
    def highlight(self, code: str) -> List[Dict]:
        tokens = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            tokens.extend(self._tokenize_line(line, line_num))
        return tokens
    def _tokenize_line(self, line: str, line_num: int) -> List[Dict]:
        tokens = []
        i = 0
        while i < len(line):
            if line[i].isspace():
                i += 1
                continue
            if line[i] == '#':
                tokens.append({'type': 'comment', 'value': line[i:], 'line': line_num, 'column': i})
                break
            if line[i] in '"\'':
                quote = line[i]
                start = i
                i += 1
                while i < len(line) and line[i] != quote:
                    if line[i] == '\\':
                        i += 2
                    else:
                        i += 1
                if i < len(line):
                    i += 1
                tokens.append({'type': 'string', 'value': line[start:i], 'line': line_num, 'column': start})
                continue
            if line[i].isalpha() or line[i] == '_':
                start = i
                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    i += 1
                word = line[start:i]
                if word in self.keywords:
                    token_type = 'keyword'
                elif word in self.builtin_functions:
                    token_type = 'builtin'
                else:
                    token_type = 'identifier'
                tokens.append({'type': token_type, 'value': word, 'line': line_num, 'column': start})
                continue
            if line[i].isdigit():
                start = i
                while i < len(line) and (line[i].isdigit() or line[i] == '.'):
                    i += 1
                tokens.append({'type': 'number', 'value': line[start:i], 'line': line_num, 'column': start})
                continue
            if line[i] in '+-*/=<>!&|^~%':
                start = i
                while i < len(line) and line[i] in '+-*/=<>!&|^~%':
                    i += 1
                tokens.append({'type': 'operator', 'value': line[start:i], 'line': line_num, 'column': start})
                continue
            if line[i] in '()[]{},:;.':
                tokens.append({'type': 'punctuation', 'value': line[i], 'line': line_num, 'column': i})
                i += 1
                continue
            i += 1
        return tokens