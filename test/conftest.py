"""Code common for all pytest modules in this package."""

import logging
from pathlib import Path
from typing import Optional

import pytest

from goth.runner.log import DEFAULT_LOG_DIR


logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """Add the optional parameter --assets-path to pytest CLI invocations."""
    parser.addoption("--assets-path", action="store")
    parser.addoption("--logs-path", action="store")


@pytest.fixture()
def assets_path(request) -> Optional[Path]:
    """Test fixture which tries to get the value of CLI parameter --assets-path.

    If the value is not set, the test using this fixture will fail.
    """

    path = request.config.option.assets_path
    if not path:
        return None

    path = Path(path)
    if not path.is_dir():
        pytest.fail("Provided assets path doesn't point to an existing directory.")

    return path.resolve()


@pytest.fixture()
def logs_path(request) -> Path:
    """Fixture which handles the CLI parameter --logs-path.

    If this parameter is not present, `DEFAULT_LOG_DIR` is used as the returned value.
    """

    path = request.config.option.logs_path

    if not path:
        return DEFAULT_LOG_DIR
    path = Path(path)
    if not path.is_dir():
        pytest.fail("Provided logs path doesn't point to an existing directory.")

    return path.resolve()


@pytest.fixture()
def project_root() -> Path:
    """Fixture that obtains the absolute path to the project's root directory.

    (assuming it's the parent directory of the current file's directory).
    """

    return Path(__file__).parent.parent.resolve()
