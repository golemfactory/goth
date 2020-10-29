"""Test the `runner.container`."""

from unittest.mock import ANY, MagicMock

from docker import DockerClient
from docker.models.containers import Container
import pytest
import transitions

from goth.runner.container import DockerContainer, State
from goth.runner.container.yagna import YagnaContainer, YagnaContainerConfig

GENERIC_COMMAND = ["cmd_name", "-f", "flag_value"]
GENERIC_ENTRYPOINT = "/usr/bin/binary_name"
GENERIC_IMAGE = "some_docker_image"
GENERIC_NAME = "generic_container"

YAGNA_CONTAINER_NAME = "yagna_container"


@pytest.fixture
def mock_container():
    """Mock a Container."""
    mock_container = MagicMock(spec=Container)
    mock_container.status = "created"
    return mock_container


@pytest.fixture
def mock_docker_client(mock_container):
    """Mock a DockerClient, `create()`` always returns a mock_container()."""
    client = MagicMock(spec=DockerClient)
    client.containers.create.return_value = mock_container
    return client


@pytest.fixture
def docker_container(mock_docker_client):
    """Create a DockerContainer, using the `mock_docker_client()`."""

    return DockerContainer(
        client=mock_docker_client,
        command=GENERIC_COMMAND,
        entrypoint=GENERIC_ENTRYPOINT,
        image=GENERIC_IMAGE,
        name=GENERIC_NAME,
    )


@pytest.fixture
def yagna_container(mock_docker_client):
    """Mock a YagnaContainer, using the `mock_docker_client()`."""
    config = MagicMock(spec=YagnaContainerConfig)
    config.name = YAGNA_CONTAINER_NAME
    config.environment = {}
    config.volumes = {}
    return YagnaContainer(mock_docker_client, config)


@pytest.mark.skip()
def test_container_create(docker_container, mock_docker_client):
    """Test if create is called on the Container, when DockerContainer() is created."""
    mock_docker_client.containers.create.assert_called_once_with(
        GENERIC_IMAGE,
        entrypoint=GENERIC_ENTRYPOINT,
        command=GENERIC_COMMAND,
        name=GENERIC_NAME,
        detach=True,
        network=DockerContainer.DEFAULT_NETWORK,
    )


def test_container_start(docker_container, mock_container):
    """Test if `start()` passed on from the DockerContainer to the Container."""
    docker_container.start()

    mock_container.start.assert_called_once()


def test_container_stop(docker_container, mock_container):
    """Test if `stop()` is passed on and the status is updated accordingly."""
    docker_container.start()

    docker_container.stop()
    mock_container.status = "exited"

    mock_container.stop.assert_called_once()
    with pytest.raises(transitions.MachineError, match=r"Can't trigger event stop.*"):
        docker_container.stop()


def test_container_remove(docker_container, mock_container):
    """Test if `remove()` is passed and the status is updated accordingly."""
    docker_container.remove()
    mock_container.status = "dead"

    mock_container.remove.assert_called_once()
    with pytest.raises(transitions.MachineError, match=r"Can't trigger event start.*"):
        docker_container.start()


def test_container_status_change(docker_container, mock_container):
    """Test if status updates are passed from the Container to the DockerContainer.

    Test that `DockerContainer` reports correct state in case of external changes to the
    status of the underlying `Container` instance.
    """

    assert docker_container.state is State.created

    mock_container.status = "dead"

    assert docker_container.state is State.dead


@pytest.mark.skip()
def test_yagna_container_create(yagna_container, mock_docker_client):
    """Test if create is called on the DockerClient when a YagnaContainer is created."""
    mock_docker_client.containers.create.assert_called_once_with(
        YagnaContainer.IMAGE,
        entrypoint=YagnaContainer.ENTRYPOINT,
        command=YagnaContainer.COMMAND,
        name=YAGNA_CONTAINER_NAME,
        environment={},
        network=DockerContainer.DEFAULT_NETWORK,
        ports=ANY,
        volumes=ANY,
        detach=True,
    )
