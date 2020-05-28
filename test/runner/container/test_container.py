from unittest.mock import ANY, MagicMock

from docker import DockerClient
import pytest
import transitions

from src.runner.container import DockerContainer, State, YagnaContainer

GENERIC_COMMAND = ["cmd_name", "-f", "flag_value"]
GENERIC_ENTRYPOINT = "/usr/bin/binary_name"
GENERIC_IMAGE = "some_docker_image"
GENERIC_NAME = "generic_container"

YAGNA_CONTAINER_NAME = "yagna_container"


@pytest.fixture
def docker_client():
    return MagicMock(spec=DockerClient)


@pytest.fixture
def docker_container(docker_client):
    return DockerContainer(
        client=docker_client,
        command=GENERIC_COMMAND,
        entrypoint=GENERIC_ENTRYPOINT,
        image=GENERIC_IMAGE,
        name=GENERIC_NAME,
        log_to_file=False,
    )


@pytest.fixture
def yagna_container(docker_client):
    config = MagicMock(spec=YagnaContainer.Config)
    config.name = YAGNA_CONTAINER_NAME
    config.environment = {}
    config.volumes = {}
    return YagnaContainer(docker_client, config)


def test_container_create(docker_container, docker_client):
    assert docker_container.state is State.created
    docker_client.containers.create.assert_called_once_with(
        GENERIC_IMAGE,
        entrypoint=GENERIC_ENTRYPOINT,
        command=GENERIC_COMMAND,
        name=GENERIC_NAME,
        detach=True,
        network=DockerContainer.DEFAULT_NETWORK,
    )


def test_container_start(docker_container):
    docker_container.start()

    assert docker_container.state is State.started
    docker_container._container.start.assert_called_once()


def test_container_stop(docker_container):
    docker_container.start()

    docker_container.stop()

    assert docker_container.state is State.stopped
    docker_container._container.stop.assert_called_once()
    with pytest.raises(transitions.MachineError, match=r"Can't trigger event stop.*"):
        docker_container.stop()


def test_container_remove(docker_container):
    docker_container.remove()

    assert docker_container.state is State.removed
    docker_container._container.remove.assert_called_once()
    with pytest.raises(transitions.MachineError, match=r"Can't trigger event start.*"):
        docker_container.start()


def test_yagna_container_create(yagna_container, docker_client):
    assert yagna_container.state is State.created
    docker_client.containers.create.assert_called_once_with(
        YagnaContainer.IMAGE,
        entrypoint=YagnaContainer.ENTRYPOINT,
        command=YagnaContainer.COMMAND,
        name=YAGNA_CONTAINER_NAME,
        environment=[],
        network=DockerContainer.DEFAULT_NETWORK,
        ports=ANY,
        volumes={},
        detach=True,
    )
