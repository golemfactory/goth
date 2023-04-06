"""Test the `runner.container.utils` module."""

from unittest.mock import MagicMock

from docker import DockerClient
from docker.models.containers import Container
import pytest

from goth.runner.container.utils import get_container_address, DockerContainer
from goth.runner.exceptions import ContainerNotFoundError

TEST_CONTAINER_NAME = "mock_container_name"
TEST_IP_ADDRESS = "172.19.0.255"


@pytest.fixture
def mock_container():
    """Mock a Container, set `attrs` field to include mock network info."""
    mock_container = MagicMock(spec=Container)
    mock_container.attrs = {
        "NetworkSettings": {
            "Networks": {
                DockerContainer.DEFAULT_NETWORK: {
                    "IPAddress": TEST_IP_ADDRESS,
                    "Aliases": [],
                }
            }
        }
    }
    return mock_container


@pytest.fixture
def mock_docker_client(mock_container):
    """Mock a DockerClient, `list()` always returns mock_container."""
    client = MagicMock(spec=DockerClient)
    client.containers.list.return_value = [mock_container]
    return client


def test_get_container_address(mock_docker_client):
    """Test if `get_container_address` returns the expected IP address.

    Uses the default network and container names.
    """
    ip_address = get_container_address(mock_docker_client, TEST_CONTAINER_NAME)
    assert ip_address == TEST_IP_ADDRESS


def test_get_container_address_partial_name(mock_docker_client):
    """Test if `get_container_address` returns the expected IP address.

    Uses a partial container name.
    """
    ip_address = get_container_address(mock_docker_client, "mock")
    assert ip_address == TEST_IP_ADDRESS


def test_get_container_address_no_container(mock_docker_client):
    """Test if the correct exception is raised when no matching container is found."""
    mock_docker_client.containers.list.return_value = []
    with pytest.raises(ContainerNotFoundError):
        get_container_address(mock_docker_client, TEST_CONTAINER_NAME)


def test_get_container_address_no_network(mock_docker_client):
    """Test if the correct exception is raised when no matching network is found.

    Uses a modified network name, to which the returned container is not connected.
    """
    with pytest.raises(KeyError):
        get_container_address(mock_docker_client, TEST_CONTAINER_NAME, "missing_network")
