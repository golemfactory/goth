"""Code common for all pytest modules in this package."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Callable, Optional

import pytest

from goth.runner import Runner, TestFailure
from goth.runner.container.build import YagnaBuildEnvironment
from goth.runner.container.compose import ComposeConfig, DEFAULT_COMPOSE_FILE
from goth.runner.container.payment import PaymentIdPool
from goth.runner.log import configure_logging, DEFAULT_LOG_DIR


def pytest_addoption(parser):
    """Add optional parameters to pytest CLI invocations."""
    parser.addoption(
        "--assets-path",
        action="store",
        help="path to custom assets to be used by yagna containers",
    )
    parser.addoption(
        "--deb-package",
        action="store",
        help="path to local .deb file or dir with .deb packages to be installed in \
                yagna containers",
    )
    parser.addoption(
        "--logs-path",
        action="store",
        help="path under which all test run logs should be stored",
    )
    parser.addoption(
        "--yagna-binary-path",
        action="store",
        help="path to local directory or archive containing yagna binaries",
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
    parser.addoption(
        "--yagna-release",
        action="store",
        help="release tag substring specifying which yagna release should be used. \
                If this is equal to 'latest', latest yagna release will be used.",
    )


@pytest.fixture(scope="session")
def deb_package(request) -> Optional[Path]:
    """Fixture that passes the --deb-package CLI parameter to the test suite."""
    deb_path = request.config.option.deb_package
    if deb_path:
        return Path(deb_path)
    return None


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
    base_log_dir = base_log_dir / f"goth_{date_str}"
    base_log_dir.mkdir(parents=True)

    configure_logging(base_log_dir)

    return base_log_dir


@pytest.fixture(scope="session")
def yagna_binary_path(request) -> Optional[Path]:
    """Fixture that passes the --yagna-binary-path CLI parameter to the test suite."""
    binary_path = request.config.option.yagna_binary_path
    if binary_path:
        return Path(binary_path)
    return None


@pytest.fixture(scope="session")
def yagna_branch(request) -> Optional[str]:
    """Fixture that passes the --yagna-branch CLI parameter to the test suite."""
    return request.config.option.yagna_branch


@pytest.fixture(scope="session")
def yagna_commit_hash(request) -> Optional[str]:
    """Fixture that passes the --yagna-commit-hash CLI parameter to the test suite."""
    return request.config.option.yagna_commit_hash


@pytest.fixture(scope="session")
def yagna_release(request) -> Optional[str]:
    """Fixture that passes the --yagna-release CLI parameter to the test suite."""
    return request.config.option.yagna_release


@pytest.fixture(scope="module")
def yagna_build_env(
    assets_path: Path,
    yagna_binary_path: Optional[Path],
    yagna_branch: Optional[str],
    yagna_commit_hash: Optional[str],
    deb_package: Optional[Path],
    yagna_release: Optional[str],
) -> YagnaBuildEnvironment:
    """Fixture which provides the build environment for yagna Docker images."""
    return YagnaBuildEnvironment(
        docker_dir=assets_path / "docker",
        binary_path=yagna_binary_path,
        branch=yagna_branch,
        commit_hash=yagna_commit_hash,
        deb_path=deb_package,
        release_tag=yagna_release,
    )


@pytest.fixture(scope="module")
def compose_config(yagna_build_env) -> ComposeConfig:
    """Fixture providing the configuration object for running docker-compose network.

    This fixture is intended to be overridden when using a non-default compose file for
    given set of tests.
    """
    patterns = {
        "ethereum": ".*Wallets supplied.",
        "zksync": ".*Running on http://0.0.0.0:3030/.*",
    }
    return ComposeConfig(
        build_env=yagna_build_env,
        file_path=yagna_build_env.docker_dir / DEFAULT_COMPOSE_FILE,
        log_patterns=patterns,
    )


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


@pytest.fixture(scope="module")
def proxy_assertions_module() -> str:
    """Fixture providing relative path to Python module with proxy assertions."""
    return "test.yagna.assertions.e2e_wasm_assertions"


@pytest.fixture
def payment_id_pool() -> PaymentIdPool:
    """Fixture providing a new instance of `PaymentIdPool` for each test."""
    return PaymentIdPool()


@pytest.fixture
def test_failure_callback() -> Callable[[TestFailure], None]:
    """Fail the current test but suppress the traceback."""

    def _handle_test_failure(err: TestFailure) -> None:
        pytest.fail(str(err), pytrace=False)

    return _handle_test_failure


# TODO: add the optional exception info argument to the callback
# (as returned by `sys.exc_info()`)
@pytest.fixture
def cancellation_callback() -> Callable[[], None]:
    """Fail the current test when the runner is cancelled."""

    return lambda: pytest.fail("The runner was cancelled", pytrace=False)


@pytest.fixture
def test_logs_dir(logs_path: Path) -> Path:
    """Provide a directory for all log files related to a single test case."""

    test_name = os.environ["PYTEST_CURRENT_TEST"]
    # Take only the function name of the currently running test
    test_name = test_name.split("::")[-1].split()[0]

    logs_dir = logs_path / test_name
    logs_dir.mkdir(parents=True, exist_ok=True)

    return logs_dir


@pytest.fixture
def runner(
    assets_path: Path,
    compose_config: ComposeConfig,
    test_logs_dir: Path,
    proxy_assertions_module: str,
    test_failure_callback: Callable[[TestFailure], None],
    cancellation_callback: Callable[[], None],
) -> Runner:
    """Fixture providing the `Runner` object for a test."""

    return Runner(
        proxy_assertions_module,
        test_logs_dir,
        compose_config,
        test_failure_callback,
        cancellation_callback,
        web_root_path=assets_path / "web-root",
    )
