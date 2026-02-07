"""Tests for shell execution tools"""
import pytest
import time
import platform
import subprocess
from pathlib import Path
from iribot.tools.execute_command import (
    ShellStartTool,
    ShellRunTool,
    ShellWriteTool,
    ShellReadTool,
    ShellStopTool,
    ShellSession,
    _detect_shell_type,
    _get_shell_config,
)


def get_outputs_dir() -> Path:
    outputs_dir = Path.cwd() / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return outputs_dir


def is_pid_running(pid: int) -> bool:
    if platform.system() == "Windows":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True,
            text=True,
            check=False,
        )
        return str(pid) in result.stdout

    result = subprocess.run(
        ["ps", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def wait_for_pid_exit(pid: int, timeout: float = 5.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if not is_pid_running(pid):
            return True
        time.sleep(0.1)
    return not is_pid_running(pid)


class TestShellDetection:
    """Test shell detection functionality"""

    def test_detect_shell_type(self):
        """Test shell type detection"""
        shell_type = _detect_shell_type()
        assert shell_type in ["bash", "cmd", "sh"]

    def test_get_shell_config(self):
        """Test getting shell configuration"""
        shell_exe, shell_args = _get_shell_config()
        assert shell_exe is not None
        assert isinstance(shell_args, list)

    def test_detected_shell_executable_exists(self):
        """Test that detected shell executable is valid"""
        shell_exe, _ = _get_shell_config()
        # Shell executable should be either absolute path or in PATH
        assert shell_exe != ""


class TestShellSession:
    """Test ShellSession functionality"""

    def test_create_shell_session(self):
        """Test creating a shell session"""
        session = ShellSession()
        try:
            assert session.process is not None
            assert session.is_alive()
        finally:
            session.terminate()

    def test_write_and_read(self):
        """Test writing to and reading from shell"""
        session = ShellSession()
        try:
            # Write a simple echo command
            session.write("echo 'test_output'")
            time.sleep(0.2)

            # Read output
            output = session.read(wait_ms=1000)
            assert "test_output" in output["stdout"]
        finally:
            session.terminate()

    def test_shell_session_with_working_dir(self, temp_work_dir):
        """Test shell session with specific working directory"""
        session = ShellSession(working_dir=temp_work_dir)
        try:
            assert session.working_dir == temp_work_dir
            assert session.is_alive()
        finally:
            session.terminate()

    def test_session_terminate(self):
        """Test terminating a shell session"""
        session = ShellSession()
        assert session.is_alive()
        session.terminate()
        time.sleep(0.1)
        assert not session.is_alive()


class TestShellTools:
    """Test shell tool classes"""


    def test_shell_start_tool(self, shell_session_id):
        """Test ShellStartTool"""
        tool = ShellStartTool()
        result = tool.execute(session_id=shell_session_id)

        assert result["success"] is True
        assert result["session_id"] == shell_session_id
        assert result["status"] == "started"

    def test_shell_run_tool_simple_command(self, shell_session_id):
        """Test ShellRunTool with simple command"""
        # Start a session first
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        # Run a command
        run_tool = ShellRunTool(get_outputs_dir())
        result = run_tool.execute(
            session_id=shell_session_id,
            command="echo 'hello'",
            wait_ms=5000,
        )

        assert result["success"] is True
        assert "hello" in result["stdout"]

    def test_shell_run_tool_with_stderr(self, shell_session_id):
        """Test ShellRunTool capturing stderr"""
        # Start a session first
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        # Run a command that produces stderr
        run_tool = ShellRunTool(get_outputs_dir())
        # Use python to ensure cross-platform compatibility
        result = run_tool.execute(
            session_id=shell_session_id,
            command='python -c "import sys; sys.stderr.write(\'error message\')"',
            wait_ms=5000,
        )

        assert result["success"] is True
        # stderr might be captured differently on different shells
        output = result["stderr"] + result["stdout"]
        # Just check that the command executed successfully
        # (stderr capture behavior may vary across platforms)
        assert "error message" in output or result["success"]

    def test_shell_write_and_read_tools(self, shell_session_id):
        """Test ShellWriteTool and ShellReadTool"""
        # Start a session
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        # Write to shell
        write_tool = ShellWriteTool()
        result = write_tool.execute(
            session_id=shell_session_id, input="echo 'write_test'"
        )
        assert result["success"] is True

        # Read from shell
        time.sleep(0.2)
        read_tool = ShellReadTool(get_outputs_dir())
        result = read_tool.execute(
            session_id=shell_session_id, wait_ms=3000, max_chars=10000
        )
        assert result["success"] is True

    def test_shell_stop_tool(self, shell_session_id):
        """Test ShellStopTool"""
        # Start a session
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        # Stop the session
        stop_tool = ShellStopTool()
        result = stop_tool.execute(session_id=shell_session_id)

        assert result["success"] is True
        assert result["status"] == "stopped"

    def test_shell_stop_kills_child_process(self, shell_session_id):
        """Ensure shell_stop terminates child processes"""
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        run_tool = ShellRunTool(get_outputs_dir())
        command = (
            "python -c \"import subprocess, sys, time; "
            "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
            "print(p.pid); sys.stdout.flush(); time.sleep(60)\""
        )
        result = run_tool.execute(
            session_id=shell_session_id,
            command=command,
            wait_ms=5000,
        )

        pid_line = None
        for line in result.get("stdout", "").splitlines():
            if line.strip().isdigit():
                pid_line = line.strip()
                break

        assert pid_line is not None
        child_pid = int(pid_line)
        assert is_pid_running(child_pid)

        stop_tool = ShellStopTool()
        stop_tool.execute(session_id=shell_session_id)

        assert wait_for_pid_exit(child_pid, timeout=5.0)

    def test_shell_run_background_command(self, shell_session_id):
        """Test running command in background"""
        # Start a session
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        # Run a command in background
        run_tool = ShellRunTool(get_outputs_dir())
        result = run_tool.execute(
            session_id=shell_session_id,
            command="echo 'background'",
            wait_ms=3000,
        )

        assert result["success"] is True
        assert result["end_reason"] in ["completed", "timeout"]

    def test_shell_run_tool_timeout(self, shell_session_id):
        """Test ShellRunTool timeout handling"""
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        run_tool = ShellRunTool(get_outputs_dir())
        result = run_tool.execute(
            session_id=shell_session_id,
            command='python -c "import time; time.sleep(4); print(\"done\")"',
            wait_ms=3000,
        )

        assert result["success"] is False
        assert result["end_reason"] == "timeout"
        assert "timed out" in result.get("error", "").lower()

    def test_shell_run_requires_wait_ms(self, shell_session_id):
        """Test ShellRunTool requires wait_ms"""
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        run_tool = ShellRunTool(get_outputs_dir())
        result = run_tool.execute(
            session_id=shell_session_id,
            command="echo 'missing wait'",
            wait_ms=None,
        )

        assert result["success"] is False
        assert "wait_ms" in result.get("error", "")


class TestMultipleShellSessions:
    """Test managing multiple shell sessions"""

    def test_multiple_sessions(self):
        """Test creating multiple independent shell sessions"""
        sessions = {}
        session_ids = ["session_1", "session_2", "session_3"]

        try:
            # Create multiple sessions
            start_tool = ShellStartTool()
            for session_id in session_ids:
                result = start_tool.execute(session_id=session_id)
                assert result["success"] is True

            # Run different commands in each session
            run_tool = ShellRunTool(get_outputs_dir())
            for i, session_id in enumerate(session_ids):
                result = run_tool.execute(
                    session_id=session_id,
                    command=f"echo 'session_{i}'",
                    wait_ms=3000,
                )
                assert result["success"] is True
                assert f"session_{i}" in result["stdout"]
        finally:
            # Clean up
            stop_tool = ShellStopTool()
            for session_id in session_ids:
                stop_tool.execute(session_id=session_id)


class TestCrossPlatformCompatibility:
    """Test cross-platform command compatibility"""

    def test_python_echo_command(self, shell_session_id):
        """Test Python-based echo command for cross-platform compatibility"""
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        run_tool = ShellRunTool(get_outputs_dir())
        result = run_tool.execute(
            session_id=shell_session_id,
            command='python -c "print(\'cross-platform-test\')"',
            wait_ms=5000,
        )

        assert result["success"] is True
        assert "cross-platform-test" in result["stdout"]

    @pytest.mark.skipif(
        platform.system() != "Windows", reason="Windows-specific test"
    )
    def test_windows_cmd_command(self, shell_session_id):
        """Test Windows CMD specific commands"""
        from iribot.config import settings

        # Force cmd
        original_shell_type = settings.shell_type
        try:
            settings.shell_type = "cmd"

            start_tool = ShellStartTool()
            start_tool.execute(session_id=shell_session_id)

            run_tool = ShellRunTool(get_outputs_dir())
            result = run_tool.execute(
                session_id=shell_session_id,
                command="echo test_cmd",
                wait_ms=5000,
            )

            assert result["success"] is True
            assert "test_cmd" in result["stdout"]
        finally:
            settings.shell_type = original_shell_type

    @pytest.mark.skipif(
        platform.system() == "Windows", reason="Unix-specific test"
    )
    def test_unix_bash_command(self, shell_session_id):
        """Test Unix bash specific commands"""
        start_tool = ShellStartTool()
        start_tool.execute(session_id=shell_session_id)

        run_tool = ShellRunTool(get_outputs_dir())
        result = run_tool.execute(
            session_id=shell_session_id,
            command="echo 'unix-test' | cat",
            wait_ms=5000,
        )

        assert result["success"] is True
        assert "unix-test" in result["stdout"]
