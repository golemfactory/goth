"""Code common for all pytest modules in this package"""

import docker
import pytest

from src.runner.container.yagna import YagnaContainer
from src.runner.exceptions import CommandError
from src.runner.probe import Role


@pytest.fixture
def yagna_container():
    """A fixture for starting and terminating a container using the `yagna` image"""

    client = docker.from_env()
    config = YagnaContainer.Config(name="cli_test_container", role=Role.provider)
    container = YagnaContainer(client, config, log_to_file=False)
    container.start()

    yield container

    # Cleanup code run when the fixture goes out of scope
    container.remove(force=True)
