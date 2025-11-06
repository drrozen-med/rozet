"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator
from uuid import uuid4

import pytest

# Mark all tests in integration/ as integration tests
pytest_plugins = []


@pytest.fixture
def test_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory(prefix="orchestrator_test_") as tmpdir:
        test_path = Path(tmpdir)
        yield test_path
        # Cleanup happens automatically via TemporaryDirectory


@pytest.fixture
def sample_codebase(test_dir: Path) -> Path:
    """Create a sample codebase structure for testing."""
    # Create simple Python project
    (test_dir / "main.py").write_text("""
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")
    
    (test_dir / "utils.py").write_text("""
def add(a, b):
    return a + b
""")
    
    (test_dir / "config.yaml").write_text("""
app:
  name: test_app
  version: 1.0.0
""")
    
    return test_dir


@pytest.fixture
def api_key() -> str:
    """Get API key from environment or skip test."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set - skipping integration test")
    return key


@pytest.fixture
def use_real_api() -> bool:
    """Check if tests should use real API calls."""
    return os.environ.get("ORCHESTRATOR_USE_REAL_API", "false").lower() == "true"

