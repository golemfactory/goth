"""Unit tests for `goth.configuration` module."""
from pathlib import Path

import pytest

from goth.configuration import load_yaml
from goth.project import PROJECT_ROOT


@pytest.fixture()
def default_config_file() -> Path:
    """Return the path of the default config file from the default assets directory."""

    return PROJECT_ROOT / "goth" / "default-assets" / "goth-config.yml"


def test_parse_default_config(default_config_file: Path):
    """Test that the default configuration file can be successfully parsed."""

    config = load_yaml(default_config_file)
    assert config.compose_config.build_env
