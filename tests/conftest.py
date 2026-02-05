"""Pytest configuration and fixtures"""
import pytest
import shutil
import sys
from pathlib import Path

# Add parent directory to path so we can import iribot
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure .env file exists before importing iribot modules
_PROJECT_ROOT = Path(__file__).parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
_ENV_EXAMPLE_PATH = _PROJECT_ROOT / "iribot" / ".env.example"

if not _ENV_PATH.exists() and _ENV_EXAMPLE_PATH.exists():
    shutil.copyfile(_ENV_EXAMPLE_PATH, _ENV_PATH)


@pytest.fixture
def temp_work_dir(tmp_path):
    """Provide a temporary working directory"""
    return str(tmp_path)


@pytest.fixture
def shell_session_id():
    """Provide a unique session ID for each test"""
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}"
