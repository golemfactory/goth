"""Code common for all pytest modules in this package."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional

import pytest

from goth.project import DEFAULT_ASSETS_DIR
from goth.runner.container.compose import DEFAULT_COMPOSE_FILE
from goth.runner.log import configure_logging, DEFAULT_LOG_DIR


def pytest_addoption(parser):
    """Add optional parameters to pytest CLI invocations."""
    parser.addoption(
        "--assets-path",
        action="store",
        help="path to custom assets to be used by yagna containers",
    )
    parser.addoption(
        "--logs-path",
        action="store",
        help="path under which all test run logs should be stored",
    )
    parser.addoption(
        "--yagna-commit-hash",
        action="store",
        help="git commit hash of yagna .deb package to be used in the tests",
    )
    parser.addoption(
        "--yagna-deb-path",
        action="store",
        help="path to a yagna .deb package to be used in the tests",
    )


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
def exe_script(assets_path: Path) -> list:
    """Fixture which parses the exe_script.json file from `assets_path` dir."""

    exe_script_path = assets_path / "exe_script.json"
    with exe_script_path.open() as fd:
        loaded = json.load(fd)
        assert isinstance(loaded, list)
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


@pytest.fixture(scope="session")
def yagna_commit_hash(request) -> Optional[str]:
    """Fixture that passes the --yagna-commit-hash CLI parameter to the test suite."""
    return request.config.option.yagna_commit_hash


@pytest.fixture(scope="session")
def yagna_deb_path(request) -> Optional[str]:
    """Fixture that passes the --yagna-deb-path CLI parameter to the test suite."""
    return request.config.option.yagna_deb_path


@pytest.fixture(scope="session")
def compose_build_env(
    yagna_commit_hash: Optional[str], yagna_deb_path: Optional[str]
) -> dict:
    """Fixture which provides the build environment for docker-compose network."""
    env = {}
    if yagna_commit_hash:
        env["YAGNA_COMMIT_HASH"] = yagna_commit_hash
    if yagna_deb_path:
        env["YAGNA_DEB_PATH"] = yagna_deb_path
    return env


@pytest.fixture(scope="session")
def compose_file_path() -> Path:
    """Fixture which provides the path to the default docker-compose file.

    This fixture is intended to be overridden when a different compose file should be
    used for a given set of tests.
    """
    return DEFAULT_COMPOSE_FILE
