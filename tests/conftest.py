"""Pytest configuration and fixtures."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test data root
TEST_DATA_ROOT = Path(tempfile.gettempdir()) / "brandlyposter-labs-test"
TEST_DATA_ROOT.mkdir(parents=True, exist_ok=True)
os.environ["BRANDLY_DATA_ROOT"] = str(TEST_DATA_ROOT)

@pytest.fixture(autouse=True)
def reset_env():
    """Reset test environment before each test."""
    # Clear test data
    import shutil
    if TEST_DATA_ROOT.exists():
        shutil.rmtree(TEST_DATA_ROOT)
    TEST_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup after
    if TEST_DATA_ROOT.exists():
        shutil.rmtree(TEST_DATA_ROOT)