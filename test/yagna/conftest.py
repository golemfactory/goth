"""Code common for all pytest modules in this package."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional

import pytest

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
        "--yagna-branch",
        action="store",
        help="name of the branch for which the yagna binaries should be downloaded",
    )
    parser.addoption(
        "--yagna-commit-hash",
        action="store",
        help="git commit hash in yagna repo for which to download binaries",
    )


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
def yagna_branch(request) -> Optional[str]:
    """Fixture that passes the --yagna-branch CLI parameter to the test suite."""
    return request.config.option.yagna_branch


@pytest.fixture(scope="session")
def compose_build_env(
    yagna_commit_hash: Optional[str],
    yagna_branch: Optional[str],
) -> dict:
    """Fixture which provides the build environment for docker-compose network."""
    env = {}
    if yagna_commit_hash:
        env["YAGNA_COMMIT_HASH"] = yagna_commit_hash
    if yagna_branch:
        env["YAGNA_BRANCH"] = yagna_branch
    return env


@pytest.fixture(scope="session")
def compose_file_path() -> Path:
    """Fixture which provides the path to the default docker-compose file.

    This fixture is intended to be overridden when a different compose file should be
    used for a given set of tests.
    """
    return DEFAULT_COMPOSE_FILE


@pytest.fixture(scope="module")
def assets_path(request) -> Path:
    """Test fixture which tries to get the value of CLI parameter --assets-path.

    If this parameter is not present, the default "<module-dir>/assets" is used,
    where `<module-dir>` is the directory containing the module that requested
    this fixture.
    """

    path_arg = request.config.option.assets_path
    if path_arg:
        path = Path(path_arg)
    else:
        test_module_path = Path(request.module.__file__).resolve()
        path = test_module_path.parent / "assets"

    if not path.is_dir():
        pytest.fail("Provided assets path doesn't point to an existing directory.")

    return path.resolve()


@pytest.fixture(scope="module")
def exe_script(assets_path: Path) -> list:
    """Fixture which parses the exe_script.json file from `assets_path` dir."""

    exe_script_path = assets_path / "requestor" / "exe_script.json"
    with exe_script_path.open() as fd:
        loaded = json.load(fd)
        assert isinstance(loaded, list)
        return loaded


@pytest.fixture(scope="module")
def task_package_template() -> str:
    """Fixture which provides the Demand's `golem.srv.comp.task_package` property.

    The returned string contains placeholders `{web_server_addr}` and
    `{web_server_port}`. Concrete values for them should be provider by the user.
    """
    return (
        "hash://sha3:d5e31b2eed628572a5898bf8c34447644bfc4b5130cfc1e4f10aeaa1"
        ":http://{web_server_addr}:{web_server_port}/rust-wasi-tutorial.zip"
    )


@pytest.fixture(scope="module")
def demand_constraints() -> str:
    """Fixture which provides the value for the Demand's `constraints` parameter."""

    return (
        "(&"
        "(golem.inf.mem.gib>0.5)(golem.inf.storage.gib>1)"
        "(golem.com.pricing.model=linear)"
        ")"
    )
