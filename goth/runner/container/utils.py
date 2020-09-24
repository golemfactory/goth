"""Utilities related to Docker containers."""
from docker import DockerClient

from goth.runner.container import DockerContainer
from goth.runner.exceptions import ContainerNotFoundError


def get_container_address(
    client: DockerClient,
    container_name: str,
    network_name: str = DockerContainer.DEFAULT_NETWORK,
) -> str:
    """Get the IP address of a container in a given network.

    The name of the container does not have to be exact, it may be a substring.
    In case of more than one container name matching the given string, the first
    container is returned, as listed by the Docker daemon.

    Raises `ContainerNotFoundError` if no matching container is found.
    Raises `KeyError` if the container is not connected to the specified network.
    """

    matching_containers = client.containers.list(filters={"name": container_name})
    if not matching_containers:
        raise ContainerNotFoundError(container_name)

    container = matching_containers[0]
    container_networks = container.attrs["NetworkSettings"]["Networks"]
    return container_networks[network_name]["IPAddress"]
