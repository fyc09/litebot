"""Pytest configuration and fixtures"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path so we can import iribot
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_work_dir(tmp_path):
    """Provide a temporary working directory"""
    return str(tmp_path)


@pytest.fixture
def shell_session_id():
    """Provide a unique session ID for each test"""
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}"
