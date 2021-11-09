"""Fixtures providing common values for integration tests."""

from pathlib import Path
import pytest

from goth.project import PROJECT_ROOT


@pytest.fixture
def default_goth_config() -> Path:
    """Return path to default `goth-config.yml` file."""
    return PROJECT_ROOT / "goth" / "default-assets" / "goth-config.yml"
