"""Classes to help configure and create `YagnaContainer`s."""

from pathlib import Path
from string import Template
from typing import Dict, Optional, TYPE_CHECKING

from docker import DockerClient
from goth.address import (
    HOST_REST_PORT_END,
    HOST_REST_PORT_START,
    YAGNA_REST_PORT,
)
from goth.runner.container import DockerContainer, DockerContainerConfig
from goth.runner.log import LogConfig

if TYPE_CHECKING:
    from goth.runner.probe import Role


class YagnaContainerConfig(DockerContainerConfig):
    """Configuration to be used for creating a new `YagnaContainer`."""

    role: "Role"
    """Role this container has in a test scenario"""

    environment: Dict[str, str]
    """Environment variables to be set for this container"""

    def __init__(
        self,
        name: str,
        role: "Role",
        volumes: Optional[Dict[Template, str]] = None,
        log_config: Optional[LogConfig] = None,
        environment: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, volumes or {}, log_config)
        self.role = role
        self.environment = environment or {}


class YagnaContainer(DockerContainer):
    """Extension of DockerContainer to be configured for yagna daemons."""

    COMMAND = ["service", "run", "-d", "/"]
    ENTRYPOINT = "/usr/bin/yagna"
    IMAGE = "yagna-goth"

    ports: Dict[int, int] = {}
    """ Port mapping between the Docker host and the container.
        Keys are container port numbers, values are host port numbers. """
    _port_offset = 0
    """ Keeps track of assigned ports on the Docker host """

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: Optional[LogConfig] = None,
        assets_path: Optional[Path] = None,
        **kwargs,
    ):
        self.ports = {YAGNA_REST_PORT: YagnaContainer.host_http_port()}
        YagnaContainer._port_offset += 1

        super().__init__(
            client=client,
            command=self.COMMAND,
            entrypoint=self.ENTRYPOINT,
            environment=config.environment,
            image=self.IMAGE,
            log_config=log_config,
            name=config.name,
            ports=self.ports,
            volumes=config.get_volumes_spec(assets_path) if assets_path else {},
            **kwargs,
        )

    @classmethod
    def host_http_port(cls):
        """Host port for the yagna REST API running in this container.

        Raises `OverflowError` if the port to return would exceed the expected range.
        """
        next_port = HOST_REST_PORT_START + cls._port_offset
        if next_port > HOST_REST_PORT_END:
            raise OverflowError(
                f"Port range exceeded. port={next_port}, range_end={HOST_REST_PORT_END}"
            )
        return next_port
