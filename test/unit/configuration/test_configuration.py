"""Unit tests for `goth.configuration` module."""
from pathlib import Path

import pytest

from goth.configuration import load_yaml


@pytest.fixture()
def test_config_file() -> Path:
    """Return the path of the config file modified specifically for unit tests."""
    return Path(__file__).parent / "test-assets" / "goth-config.yml"


def test_parse_default_config(test_config_file: Path):
    """Test that the default configuration file can be successfully parsed."""

    config = load_yaml(test_config_file)
    assert config.compose_config.build_env


def test_load_yaml_override_existing(test_config_file: Path):
    """Test overriding an existing field in a YAML config file."""

    test_key = "zksync"
    test_value = ".*I am overridden!.*"
    overrides = [
        (f"docker-compose.compose-log-patterns.{test_key}", test_value),
    ]

    config = load_yaml(test_config_file, overrides)

    assert config.compose_config.log_patterns[test_key] == test_value


def test_load_yaml_override_new(test_config_file: Path):
    """Test adding a new field to a YAML config file through overrides."""

    test_value = "v0.0.1-rc666"
    overrides = [
        ("docker-compose.build-environment.release-tag", test_value),
    ]

    config = load_yaml(test_config_file, overrides)

    assert config.compose_config.build_env.release_tag == test_value


def test_load_yaml_override_top_level(test_config_file: Path):
    """Test overriding a value under a top-level dict in the YAML file."""

    test_value = "overridden-name"
    overrides = [
        ("web-root", test_value),
    ]

    config = load_yaml(test_config_file, overrides)

    assert config.web_root
    assert config.web_root.name == test_value


def test_load_yaml_environment(test_config_file: Path):
    """Test setting environment variables in goth-config.yml."""

    node_name = "env-var-test"
    existing_var_name = "GSB_URL"
    existing_var_value = "tcp://test:6666"
    new_var_name = "TEST_ENV_VAR"
    new_var_value = "test_value"

    config = load_yaml(test_config_file)

    node = [c for c in config.containers if c.name == node_name][0]
    assert node.environment[existing_var_name] == existing_var_value
    assert node.environment[new_var_name] == new_var_value


def test_load_yaml_override_artifacts():
    """Test overriding download configuration for additional artifacts (for example: runtimes)"""

    test_config_file = Path(__file__).parent / "test-assets" / "goth-config-artifacts-override.yml"
    config = load_yaml(test_config_file)

    assert config.compose_config.build_env.artifacts["ya-runtime-vm"].use_prerelease is True
    assert config.compose_config.build_env.artifacts["ya-runtime-vm"].release_tag == "v0.3..*"

    assert config.compose_config.build_env.artifacts["ya-runtime-wasi"].use_prerelease is False
    assert config.compose_config.build_env.artifacts["ya-runtime-wasi"].release_tag == "v0.2..*"

    assert config.compose_config.build_env.artifacts["ya-relay-server"].use_prerelease is False
    assert config.compose_config.build_env.artifacts["ya-relay-server"].release_tag is None
