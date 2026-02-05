"""Execute command tool with interactive shell sessions"""
import os
import subprocess
import platform
import threading
import time
import uuid
import shutil
from collections import deque
from typing import Any, Dict, Optional, Deque, Tuple, List
from .base import BaseTool, BaseToolGroup, BaseStatus
from ..config import settings


def _detect_shell_type() -> str:
    """Detect available shell type on the system."""
    # Check if bash is available
    bash_path = shutil.which("bash")
    if bash_path:
        return "bash"
    
    # Fall back to cmd on Windows
    if platform.system() == "Windows":
        return "cmd"
    
    # Fall back to sh on Unix-like systems
    sh_path = shutil.which("sh")
    if sh_path:
        return "sh"
    
    # Default to bash
    return "bash"


def _get_shell_config() -> Tuple[str, List[str]]:
    """Get shell executable and arguments based on configuration.
    
    Returns:
        Tuple of (executable_path, command_args_list)
    """
    shell_type = settings.shell_type
    
    # Auto-detect if shell_type is "auto"
    if shell_type == "auto":
        shell_type = _detect_shell_type()
    
    if shell_type == "cmd":
        # Windows CMD
        return "cmd.exe", ["/Q"]  # /Q disables echo
    elif shell_type == "bash":
        # Use configured bash path or find bash
        bash_cmd = settings.bash_path
        if not os.path.exists(bash_cmd) and bash_cmd == "bash":
            # Try to find bash if it's just "bash"
            bash_found = shutil.which("bash")
            if bash_found:
                bash_cmd = bash_found
        return bash_cmd, ["--norc", "--noprofile"]
    else:
        # Fallback to bash
        bash_cmd = settings.bash_path
        if not os.path.exists(bash_cmd) and bash_cmd == "bash":
            bash_found = shutil.which("bash")
            if bash_found:
                bash_cmd = bash_found
        return bash_cmd, ["--norc", "--noprofile"]


class ShellSession:
    """Persistent shell session with async output capture"""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir
        self._output: Deque[Tuple[str, str]] = deque()
        self._log: Deque[Dict[str, str]] = deque()
        self._output_event = threading.Event()
        self._lock = threading.Lock()
        self._running_marker: Optional[str] = None  # Track if command is running

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        # Use UTF-8 encoding for both Windows and Unix
        # Git Bash and Python both support UTF-8 well
        
        # Disable colors and set simple terminal to avoid ANSI escape sequences
        env["TERM"] = "dumb"
        env["PS1"] = "$ "  # Simple prompt without colors
        env["NO_COLOR"] = "1"  # Disable colors in many tools
        env["PYTHONUNBUFFERED"] = "1"  # Disable Python output buffering
        
        # Get shell executable and arguments
        shell_exe, shell_args = _get_shell_config()
        cmd = [shell_exe] + shell_args

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_dir if working_dir else None,
            text=False,  # Use binary mode to avoid line buffering issues
            bufsize=0,  # Unbuffered
            env=env,
        )

        self._stdout_thread = threading.Thread(
            target=self._read_stream,
            args=("stdout", self.process.stdout),
            daemon=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stream,
            args=("stderr", self.process.stderr),
            daemon=True,
        )
        self._stdout_thread.start()
        self._stderr_thread.start()

    def _read_stream(self, stream_name: str, stream):
        try:
            buffer = b""
            while True:
                byte = stream.read(1)
                if not byte:
                    # Stream closed
                    if buffer:
                        try:
                            text = buffer.decode('utf-8', errors='replace')
                            with self._lock:
                                self._output.append((stream_name, text))
                                self._log.append({"stream": stream_name, "data": text})
                                self._output_event.set()
                        except:
                            pass
                    break
                
                buffer += byte
                # Flush buffer when encountering newline or reaching max size
                if byte == b'\n' or len(buffer) >= 1024:
                    try:
                        text = buffer.decode('utf-8', errors='replace')
                        with self._lock:
                            self._output.append((stream_name, text))
                            self._log.append({"stream": stream_name, "data": text})
                            self._output_event.set()
                        buffer = b""
                    except:
                        buffer = b""
        except Exception:
            pass
        finally:
            stream.close()

    def is_alive(self) -> bool:
        return self.process and self.process.poll() is None

    def write(self, data: str) -> None:
        if not self.is_alive():
            raise RuntimeError("Shell session is not running")
        if not data.endswith("\n"):
            data += "\n"
        with self._lock:
            self._log.append({"stream": "stdin", "data": data})
        self.process.stdin.write(data.encode('utf-8'))
        self.process.stdin.flush()

    def read(self, wait_ms: int = 0, max_chars: int = 20000) -> Dict[str, Any]:
        output = []
        stderr = []

        if wait_ms > 0:
            self._output_event.wait(wait_ms / 1000)

        with self._lock:
            char_count = 0
            while self._output and char_count <= max_chars:
                stream_name, line = self._output.popleft()
                char_count += len(line)
                if stream_name == "stdout":
                    output.append(line)
                else:
                    stderr.append(line)
            self._output_event.clear()

        return {
            "stdout": "".join(output),
            "stderr": "".join(stderr),
        }

    def terminate(self) -> None:
        if self.is_alive():
            self.process.terminate()

    def get_log(self) -> list:
        with self._lock:
            return list(self._log)
    
    def is_running(self) -> bool:
        """Check if a command is currently running (marker not yet seen)"""
        if self._running_marker is None:
            return False
        
        # Check if marker is already in the buffered stdout
        # This handles the case where command completed but we didn't wait long enough
        with self._lock:
            stdout_text = "".join(
                data for stream_name, data in self._output if stream_name == "stdout"
            )
            marker_index = stdout_text.find(self._running_marker)
            if marker_index != -1:
                # Remove marker from stdout buffer while preserving other output
                stdout_without_marker = (
                    stdout_text[:marker_index]
                    + stdout_text[marker_index + len(self._running_marker):]
                )

                new_output = deque()
                stdout_pos = 0
                for stream_name, data in self._output:
                    if stream_name == "stdout":
                        if stdout_pos >= len(stdout_without_marker):
                            continue
                        take_len = min(len(data), len(stdout_without_marker) - stdout_pos)
                        chunk = stdout_without_marker[stdout_pos:stdout_pos + take_len]
                        stdout_pos += take_len
                        if chunk:
                            new_output.append((stream_name, chunk))
                    else:
                        new_output.append((stream_name, data))

                self._output = new_output
                self._running_marker = None
                return False
        
        return True
    
    def set_running_marker(self, marker: str) -> None:
        """Set the marker for currently running command"""
        with self._lock:
            self._running_marker = marker
    
    def clear_running_marker(self) -> None:
        """Clear the running marker when command completes"""
        with self._lock:
            self._running_marker = None


_shell_sessions: Dict[str, ShellSession] = {}


def _collect_output_until_marker(
    session: ShellSession,
    marker: str,
    wait_ms: int,
    max_chars: int,
) -> Tuple[str, str, bool]:
    """
    Collect output from session until marker is found or timeout.
    
    Returns: (stdout, stderr, marker_found)
    """
    max_wait_time = wait_ms if wait_ms > 0 else 100000
    start_time = time.time() * 1000
    all_stdout = []
    all_stderr = []
    marker_found = False
    accumulated_stdout = ""

    while (time.time() * 1000 - start_time) < max_wait_time:
        output = session.read(wait_ms=100, max_chars=max_chars)
        stdout_chunk = output.get("stdout", "")
        stderr_chunk = output.get("stderr", "")

        if stdout_chunk:
            accumulated_stdout += stdout_chunk

        if stderr_chunk:
            all_stderr.append(stderr_chunk)

        # Check for marker in accumulated output
        if accumulated_stdout:
            marker_index = accumulated_stdout.find(marker)
            if marker_index != -1:
                marker_found = True
                all_stdout.append(accumulated_stdout[:marker_index])
                accumulated_stdout = ""
                session.clear_running_marker()
                break

        if not stdout_chunk and not stderr_chunk:
            time.sleep(0.01)

    # Add any remaining output
    if accumulated_stdout:
        all_stdout.append(accumulated_stdout)

    return "".join(all_stdout), "".join(all_stderr), marker_found


def _ensure_session(session_id: str, working_dir: Optional[str] = None) -> ShellSession:
    if session_id not in _shell_sessions or not _shell_sessions[session_id].is_alive():
        _shell_sessions[session_id] = ShellSession(working_dir=working_dir)
        if working_dir:
            _shell_sessions[session_id].write(f'cd "{working_dir}"')
    return _shell_sessions[session_id]


def _get_sessions_status() -> List[Dict[str, Any]]:
    sessions = []
    for session_id, session in _shell_sessions.items():
        sessions.append({
            "session_id": session_id,
            "working_dir": session.working_dir,
            "alive": session.is_alive(),
            "pid": session.process.pid if session.process else None,
            "log": session.get_log(),
        })
    return sessions


class ShellStartTool(BaseTool):
    """Start a persistent shell session (bash or cmd depending on system)"""

    @property
    def name(self) -> str:
        return "shell_start"

    @property
    def description(self) -> str:
        return "Start a persistent shell session. On Windows, uses cmd.exe if bash is unavailable; on Unix-like systems, uses bash or sh."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session/agent identifier for persistent shell",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory to start shell (optional)",
                },
            },
            "required": [],
        }

    def execute(
        self,
        session_id: Optional[str] = None,
        working_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        session_id = session_id or "default"
        _ensure_session(session_id, working_dir=working_dir)
        return {
            "success": True,
            "session_id": session_id,
            "status": "started",
        }


class ShellRunTool(BaseTool):
    """Run a command in a shell session"""

    @property
    def name(self) -> str:
        return "shell_run"

    @property
    def description(self) -> str:
        return "Run a command in a persistent shell session (bash or cmd). **IMPORTANT**: If 'background' is set to true, the command will run in the background and the tool will return immediately. This will occupy the shell session; start a new session for other commands."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session/agent identifier for persistent shell",
                },
                "command": {
                    "type": "string",
                    "description": "Command to run",
                },
                "wait_ms": {
                    "type": "integer",
                    "description": "Max wait time in milliseconds for command completion",
                    "default": 10000,
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Max characters to return from buffered output",
                    "default": 20000,
                },
                "background": {
                    "type": "boolean",
                    "description": "Run command in background and return immediately. **IMPORTANT** This will occupy the shell session; start a new session for other commands.",
                    "default": False,
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory to start shell (optional)",
                },
            },
            "required": ["command", "background"],
        }

    def execute(
        self,
        command: str,
        session_id: Optional[str] = None,
        wait_ms: Optional[int] = None,
        max_chars: int = 20000,
        background: bool = False,
        working_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        session_id = session_id or "default"
        session = _ensure_session(session_id, working_dir=working_dir)

        # Check if session is already running a command
        if session.is_running():
            return {
                "success": False,
                "error": f"Session '{session_id}' is already running a command. Please wait for it to complete, use shell_read to check status, or start a new session to run another command.",
                "session_id": session_id,
            }

        if wait_ms is None:
            wait_ms = 10000 if background else 100000

        marker = f"__CMD_DONE_{uuid.uuid4().hex[:8]}__"
        
        # Mark session as running before executing command
        session.set_running_marker(marker)

        session.write(command)
        session.write(f"echo {marker}")

        if background:
            # For background mode, wait for marker with a reasonable timeout
            # If marker is found, command completed and marker will be cleared
            # If marker is not found, command is still running, keep marker set
            # (is_running() will check buffer for marker before rejecting new commands)
            stdout, stderr, marker_found = _collect_output_until_marker(
                session, marker, wait_ms, max_chars
            )
            
            status = "completed" if marker_found else "running"
            
            return {
                "success": True,
                "session_id": session_id,
                "status": status,
                "stdout": stdout,
                "stderr": stderr,
            }
        else:
            # For normal mode, wait until completion or timeout
            max_wait_time = wait_ms if wait_ms > 0 else 100000
            stdout, stderr, marker_found = _collect_output_until_marker(
                session, marker, max_wait_time, max_chars
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "stdout": stdout,
                "stderr": stderr,
            }


class ShellWriteTool(BaseTool):
    """Write input to a shell session"""

    @property
    def name(self) -> str:
        return "shell_write"

    @property
    def description(self) -> str:
        return "Write input to stdin of a persistent shell session (bash or cmd)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session/agent identifier for persistent shell",
                },
                "input": {
                    "type": "string",
                    "description": "Input to write to stdin",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory to start shell (optional)",
                },
            },
            "required": ["input"],
        }

    def execute(
        self,
        input: str,
        session_id: Optional[str] = None,
        working_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        session_id = session_id or "default"
        session = _ensure_session(session_id, working_dir=working_dir)
        session.write(input)
        return {
            "success": True,
            "session_id": session_id,
        }


class ShellReadTool(BaseTool):
    """Read output from a shell session"""

    @property
    def name(self) -> str:
        return "shell_read"

    @property
    def description(self) -> str:
        return "Read buffered output from a persistent shell session (bash or cmd)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session/agent identifier for persistent shell",
                },
                "wait_ms": {
                    "type": "integer",
                    "description": "Wait time in milliseconds before reading output",
                    "default": 0,
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Max characters to return from buffered output",
                    "default": 20000,
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory to start shell (optional)",
                },
            },
            "required": [],
        }

    def execute(
        self,
        session_id: Optional[str] = None,
        wait_ms: int = 0,
        max_chars: int = 20000,
        working_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        session_id = session_id or "default"
        session = _ensure_session(session_id, working_dir=working_dir)
        default_wait_ms = wait_ms if wait_ms > 0 else 1000
        output = session.read(wait_ms=default_wait_ms, max_chars=max_chars)
        return {
            "success": True,
            "session_id": session_id,
            **output,
        }


class ShellStopTool(BaseTool):
    """Stop a shell session"""

    @property
    def name(self) -> str:
        return "shell_stop"

    @property
    def description(self) -> str:
        return "Stop a persistent shell session (bash or cmd)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session/agent identifier for persistent shell",
                },
            },
            "required": [],
        }

    def execute(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        session_id = session_id or "default"
        session = _shell_sessions.get(session_id)
        if not session or not session.is_alive():
            return {
                "success": True,
                "session_id": session_id,
                "status": "stopped",
            }
        session.terminate()
        return {
            "success": True,
            "session_id": session_id,
            "status": "stopped",
        }


class ShellToolGroup(BaseToolGroup):
    """Shell tool group"""

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Persistent shell tools (bash or cmd depending on system availability)."

    def get_tools(self) -> List[BaseTool]:
        return [
            ShellStartTool(),
            ShellRunTool(),
            ShellWriteTool(),
            ShellReadTool(),
            ShellStopTool(),
        ]


class ShellStatus(BaseStatus):
    """Status provider for shell sessions"""

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Persistent shell (bash/cmd) status."

    def get_status(self) -> Dict[str, Any]:
        shell_exe, _ = _get_shell_config()
        return {
            "name": self.name,
            "status": "ok",
            "shell_executable": shell_exe,
            "sessions": _get_sessions_status(),
        }
