"""Code common for all pytest modules in this package."""

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from goth.project import DEFAULT_ASSETS_DIR
from goth.runner.log import configure_logging, DEFAULT_LOG_DIR


def pytest_addoption(parser):
    """Add the optional parameter --assets-path to pytest CLI invocations."""
    parser.addoption("--assets-path", action="store")
    parser.addoption("--logs-path", action="store")


@pytest.fixture(scope="session")
def assets_path(request) -> Path:
    """Test fixture which tries to get the value of CLI parameter --assets-path.

    If this parameter is not present, `DEFAULT_ASSETS_DIR` is used as the return value.
    """

    path = request.config.option.assets_path
    if not path:
        return DEFAULT_ASSETS_DIR

    path = Path(path)
    if not path.is_dir():
        pytest.fail("Provided assets path doesn't point to an existing directory.")

    return path.resolve()


@pytest.fixture(scope="session")
def exe_script(assets_path: Path) -> dict:
    """Fixture which parses the exe_script.json file from `assets_path` dir."""

    exe_script_path = assets_path / "exe_script.json"
    with exe_script_path.open() as fd:
        loaded = json.load(fd)
        assert isinstance(loaded, dict)
        return loaded


@pytest.fixture(scope="session")
def logs_path(request) -> Path:
    """Fixture which handles the CLI parameter --logs-path.

    This also creates a common base log directory for all tests within a given session.
    If --logs-path is not present, `DEFAULT_LOG_DIR` is used as the returned value.
    """

    logs_path: str = request.config.option.logs_path
    base_log_dir = Path(logs_path) if logs_path else DEFAULT_LOG_DIR
    base_log_dir = base_log_dir.resolve()

    # Create a unique subdirectory for this test run
    date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
    base_log_dir = base_log_dir / f"yagna_integration_{date_str}"
    base_log_dir.mkdir(parents=True)

    configure_logging(base_log_dir)

    return base_log_dir
