"""Code common for all pytest modules in this package"""

import time

import docker
import pytest

from goth.runner.container.yagna import YagnaContainer, YagnaContainerConfig
from goth.runner.exceptions import CommandError
from goth.runner.log import LogConfig
from goth.runner.probe import Role


@pytest.fixture
def yagna_container():
    """A fixture for starting and terminating a container using the `yagna` image"""

    client = docker.from_env()
    config = YagnaContainerConfig(name="cli_test_container", role=Role.provider)
    container = YagnaContainer(client, config)
    container.start()
    # Give the daemon some time to start serving requests
    time.sleep(1.0)

    yield container

    # Cleanup code run when the fixture goes out of scope
    container.remove(force=True)
