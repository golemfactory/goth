"""Utilities related to Docker containers."""
from pathlib import Path
from typing import Dict

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


def get_volumes_spec(
    volumes: Dict[Path, str], writable: bool = True
) -> Dict[str, dict]:
    """Generate Docker volume specification based on a list of directory mappings.

    `volumes` argument contains mappings between directories. Keys are paths on host,
    values are mount points in the container.
    When `writable` is `True`, the volumes will be mounted as read/write, granting
    the container with write permissions on the mount point.
    """
    return {
        str(host_path.resolve()): {
            "bind": mount_path,
            "mode": "rw" if writable else "ro",
        }
        for host_path, mount_path in volumes.items()
    }
