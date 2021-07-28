"""Fixtures providing common values for integration tests."""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from goth.project import PROJECT_ROOT


@pytest.fixture
def log_dir() -> Path:
    """Return path to dir where goth test session logs should be placed."""
    base_dir = Path("/", "tmp", "goth-tests")
    date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
    log_dir = base_dir / f"goth_{date_str}"
    log_dir.mkdir(parents=True)
    return log_dir


@pytest.fixture
def default_goth_config() -> Path:
    """Return path to default `goth-config.yml` file."""
    return PROJECT_ROOT / "goth" / "default-assets" / "goth-config.yml"
