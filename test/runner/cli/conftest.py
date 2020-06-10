"""Code common for all pytest modules in this package"""

import docker
import pytest

from src.runner.container.yagna import YagnaContainer, YagnaContainerConfig
from src.runner.exceptions import CommandError
from src.runner.log import LogConfig
from src.runner.probe import Role


@pytest.fixture
def yagna_container():
    """A fixture for starting and terminating a container using the `yagna` image"""

    client = docker.from_env()
    config = YagnaContainerConfig(name="cli_test_container", role=Role.provider)
    container = YagnaContainer(client, config)
    container.start()

    yield container

    # Cleanup code run when the fixture goes out of scope
    container.remove(force=True)
