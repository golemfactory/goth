"""Code common for all pytest modules in this package."""

from docker import DockerClient
from docker.models.containers import Container
import pytest
from unittest.mock import MagicMock

from .mock import MockYagnaCLI
from goth.runner.container import DockerContainer
from goth.runner.container.yagna import YagnaContainer, YagnaContainerConfig

GENERIC_COMMAND = ["cmd_name", "-f", "flag_value"]
GENERIC_ENTRYPOINT = "/usr/bin/binary_name"
GENERIC_IMAGE = "some_docker_image"
GENERIC_NAME = "generic_container"
YAGNA_CONTAINER_NAME = "yagna_container"


@pytest.fixture
def mock_yagna_cli():
    """Mock a yagna CLI."""
    return MockYagnaCLI()


@pytest.fixture
def mock_container(mock_yagna_cli):
    """Mock a Container."""
    mock_container = MagicMock(spec=Container)
    mock_container.status = "created"
    mock_container.exec_run = mock_yagna_cli.exec_run
    return mock_container


@pytest.fixture
def mock_docker_client(mock_container):
    """Mock a DockerClient, `create()`` always returns a mock_container()."""
    client = MagicMock(spec=DockerClient)
    client.containers.create.return_value = mock_container
    return client


@pytest.fixture
def docker_container(mock_docker_client, mock_container):
    """Create a DockerContainer, using the `mock_docker_client()`."""
    mock_docker_client.containers.create.return_value = mock_container
    return DockerContainer(
        client=mock_docker_client,
        command=GENERIC_COMMAND,
        entrypoint=GENERIC_ENTRYPOINT,
        image=GENERIC_IMAGE,
        name=GENERIC_NAME,
    )


@pytest.fixture
def yagna_container(mock_docker_client):
    """Fixture for starting and terminating a container using the `yagna` image."""
    config = MagicMock(spec=YagnaContainerConfig)
    config.name = YAGNA_CONTAINER_NAME
    config.environment = {}
    config.volumes = {}
    return YagnaContainer(mock_docker_client, config)
