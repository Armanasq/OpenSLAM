#!/usr/bin/env python3

import asyncio
import subprocess
import os
import pty
import select
import termios
import struct
import fcntl
import signal
import threading
from typing import Dict, Optional, Callable

class TerminalSession:
    def __init__(self, session_id: str, cwd: str = None):
        self.session_id = session_id
        self.cwd = cwd or os.getcwd()
        self.process = None
        self.master_fd = None
        self.slave_fd = None
        self.is_active = False
        self.output_callback = None
        
    def start(self):
        """Start a new terminal session with PTY"""
        try:
            # Create a pseudo-terminal
            self.master_fd, self.slave_fd = pty.openpty()
            
            # Set terminal size
            self._set_terminal_size(120, 30)
            
            # Start bash process with proper environment
            env = os.environ.copy()
            env['TERM'] = 'xterm-256color'
            env['PS1'] = '\\u@\\h:\\w$ '
            
            self.process = subprocess.Popen(
                ['/bin/bash', '--login'],
                stdin=self.slave_fd,
                stdout=self.slave_fd,
                stderr=self.slave_fd,
                cwd=self.cwd,
                env=env,
                preexec_fn=os.setsid
            )
            
            # Close slave fd in parent process
            os.close(self.slave_fd)
            
            # Make master fd non-blocking
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, os.O_NONBLOCK)
            
            self.is_active = True
            
            # Start output monitoring thread
            self.output_thread = threading.Thread(target=self._monitor_output, daemon=True)
            self.output_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Failed to start terminal session: {e}")
            return False
    
    def _set_terminal_size(self, cols: int, rows: int):
        """Set terminal window size"""
        if self.master_fd:
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
    
    def write_command(self, command: str):
        """Write command to terminal"""
        if self.master_fd and self.is_active:
            try:
                os.write(self.master_fd, (command + '\r').encode('utf-8'))
            except Exception as e:
                print(f"Failed to write command: {e}")
    
    def _monitor_output(self):
        """Monitor terminal output in separate thread"""
        while self.is_active and self.master_fd:
            try:
                # Check if data is available
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                if ready:
                    data = os.read(self.master_fd, 4096)
                    if data and self.output_callback:
                        output = data.decode('utf-8', errors='ignore')
                        # Run callback in thread-safe way
                        asyncio.run_coroutine_threadsafe(
                            self.output_callback(output),
                            asyncio.get_event_loop()
                        )
            except (OSError, BlockingIOError):
                continue
            except Exception as e:
                print(f"Output monitoring error: {e}")
                break
    
    def resize(self, cols: int, rows: int):
        """Resize terminal"""
        self._set_terminal_size(cols, rows)
    
    def close(self):
        """Close terminal session"""
        self.is_active = False
        
        if self.process:
            try:
                # Send SIGTERM to process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=5)
            except:
                try:
                    # Force kill if needed
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except:
                    pass
        
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except:
                pass

class TerminalManager:
    def __init__(self):
        self.sessions: Dict[str, TerminalSession] = {}
    
    def create_session(self, session_id: str, cwd: str = None) -> bool:
        """Create a new terminal session"""
        if session_id in self.sessions:
            self.close_session(session_id)
        
        session = TerminalSession(session_id, cwd)
        success = session.start()
        
        if success:
            self.sessions[session_id] = session
        
        return success
    
    def execute_command(self, session_id: str, command: str):
        """Execute command in terminal session"""
        if session_id in self.sessions:
            self.sessions[session_id].write_command(command)
    
    def set_output_callback(self, session_id: str, callback: Callable):
        """Set callback for terminal output"""
        if session_id in self.sessions:
            self.sessions[session_id].output_callback = callback
    
    def close_session(self, session_id: str):
        """Close terminal session"""
        if session_id in self.sessions:
            self.sessions[session_id].close()
            del self.sessions[session_id]
    
    def close_all_sessions(self):
        """Close all terminal sessions"""
        for session_id in list(self.sessions.keys()):
            self.close_session(session_id)

# Global terminal manager instance
terminal_manager = TerminalManager()