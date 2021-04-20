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


def test_load_yaml_override_existing(default_config_file: Path):
    """Test overriding an existing field in a YAML config file."""

    test_key = "zksync"
    test_value = ".*I am overridden!.*"
    overrides = [
        (f"docker-compose.compose-log-patterns.{test_key}", test_value),
    ]

    config = load_yaml(default_config_file, overrides)

    assert config.compose_config.log_patterns[test_key] == test_value


def test_load_yaml_override_new(default_config_file: Path):
    """Test adding a new field to a YAML config file through overrides."""

    test_value = "v0.0.1-rc666"
    overrides = [
        ("docker-compose.build-environment.release-tag", test_value),
    ]

    config = load_yaml(default_config_file, overrides)

    assert config.compose_config.build_env.release_tag == test_value


def test_load_yaml_override_top_level(default_config_file: Path):
    """Test overriding a value under a top-level dict in the YAML file."""

    test_value = "overridden-name"
    overrides = [
        ("web-root", test_value),
    ]

    config = load_yaml(default_config_file, overrides)

    assert config.web_root
    assert config.web_root.name == test_value
