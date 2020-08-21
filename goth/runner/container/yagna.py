"""Classes to help configure and create `YagnaContainer`s."""

from pathlib import Path
from string import Template
from typing import ClassVar, Dict, Iterator, Optional, TYPE_CHECKING

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

    use_requestor_agent: bool
    """Indicates whether ya-requestor should be started by the given node.

    This config field exists for the sake of backwards compatibility with the level 0
    test scenario. It is consumed only by requestor nodes.
    """

    key_file: Optional[str]
    """Keyfile to be imported into the yagna id service."""

    def __init__(
        self,
        name: str,
        role: "Role",
        volumes: Optional[Dict[Template, str]] = None,
        log_config: Optional[LogConfig] = None,
        environment: Optional[Dict[str, str]] = None,
        key_file: Optional[str] = None,
        use_requestor_agent: bool = False,
    ):
        super().__init__(name, volumes or {}, log_config)
        self.role = role
        self.environment = environment or {}
        self.key_file = key_file
        self.use_requestor_agent = use_requestor_agent


class YagnaContainer(DockerContainer):
    """Extension of DockerContainer to be configured for yagna daemons."""

    COMMAND = ["service", "run", "-d", "/"]
    ENTRYPOINT = "/usr/bin/yagna"
    IMAGE = "yagna-goth"

    ports: Dict[int, int] = {}
    """ Port mapping between the Docker host and the container.
        Keys are container port numbers, values are host port numbers. """

    host_port_range: ClassVar[Iterator[int]] = iter(
        range(HOST_REST_PORT_START, HOST_REST_PORT_END)
    )
    """ Keeps track of assigned ports on the Docker host """

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: Optional[LogConfig] = None,
        assets_path: Optional[Path] = None,
        **kwargs,
    ):
        self.ports = {YAGNA_REST_PORT: YagnaContainer.host_rest_port()}

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
    def host_rest_port(cls):
        """Return the next host port that can be used for port mapping.

        Raises `OverflowError` if the port to return would exceed the expected range.
        """
        try:
            return next(cls.host_port_range)
        except StopIteration:
            raise OverflowError(f"Port range exceeded. range_end={HOST_REST_PORT_END}")
