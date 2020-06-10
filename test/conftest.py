from pathlib import Path
import pytest

from src.runner.log import DEFAULT_LOG_DIR


def pytest_addoption(parser):
    """ Adds the optional parameter --assets-path to pytest CLI invocations. """
    parser.addoption("--assets-path", action="store")
    parser.addoption("--logs-path", action="store")


@pytest.fixture()
def assets_path(request) -> Path:
    """ Test fixture which tries to get the value of CLI parameter --assets-path.
        If the value is not set, the test using this fixture will fail. """
    path = request.config.option.assets_path
    if not path:
        pytest.fail("The CLI option --assets-path was not provided.")

    path = Path(path)
    if not path.is_dir():
        pytest.fail("Provided assets path doesn't point to an existing directory.")

    return path.resolve()


@pytest.fixture()
def logs_path(request) -> Path:
    """ Fixture which handles the CLI parameter --logs-path. If this parameter is not
        present, `DEFAULT_LOG_DIR` is used as the returned value. """
    path = request.config.option.logs_path

    if not path:
        return DEFAULT_LOG_DIR
    path = Path(path)
    if not path.is_dir():
        pytest.fail("Provided logs path doesn't point to an existing directory.")

    return path.resolve()
