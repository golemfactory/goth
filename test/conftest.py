from pathlib import Path
from typing import Optional

import pytest


def pytest_addoption(parser):
    """ Adds the optional parameter --assets-path to pytest CLI invocations. """
    parser.addoption("--assets-path", action="store")


@pytest.fixture()
def assets_path(request) -> Optional[Path]:
    """ Test fixture which tries to get the value of CLI parameter --assets-path.
        If the value is not set, the test using this fixture will fail. """
    path = request.config.option.assets_path
    if not path:
        return None

    path = Path(path)
    if not path.is_dir():
        pytest.fail("Provided assets path doesn't point to an existing directory.")

    return path.resolve()
