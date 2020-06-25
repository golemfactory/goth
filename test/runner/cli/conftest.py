"""Code common for all pytest modules in this package"""
from unittest.mock import MagicMock

import time

from docker import DockerClient
from docker.models.containers import Container
import docker
import pytest

from src.runner.container import DockerContainer
from src.runner.container.yagna import YagnaContainer, YagnaContainerConfig
from src.runner.exceptions import CommandError
from src.runner.log import LogConfig
from src.runner.probe import Role

GENERIC_COMMAND = ["cmd_name", "-f", "flag_value"]
GENERIC_ENTRYPOINT = "/usr/bin/binary_name"
GENERIC_IMAGE = "some_docker_image"
GENERIC_NAME = "generic_container"

YAGNA_CONTAINER_NAME = "yagna_container"

@pytest.fixture
def mock_container():
    mock_container = MagicMock(spec=Container)
    mock_container.status = "created"
    return mock_container

@pytest.fixture
def mock_docker_client(mock_container):
    client = MagicMock(spec=DockerClient)
    client.containers.create.return_value = mock_container
    return client

@pytest.fixture
def docker_container(mock_docker_client):
    mock_docker_client.containers.create.return_value = mock_container
    return DockerContainer(
        client=mock_docker_client,
        command=GENERIC_COMMAND,
        entrypoint=GENERIC_ENTRYPOINT,
        image=GENERIC_IMAGE,
        name=GENERIC_NAME,
    )

@pytest.fixture
def yagna_container():
    """A fixture for starting and terminating a container using the `yagna` image"""

    config = MagicMock(spec=YagnaContainerConfig)
    config.name = YAGNA_CONTAINER_NAME
    config.environment = {}
    config.volumes = {}
    container = YagnaContainer(mock_docker_client, config)
    container.start()
    # Give the daemon some time to start serving requests
    time.sleep(1.0)

    yield container

    # Cleanup code run when the fixture goes out of scope
    container.remove(force=True)
