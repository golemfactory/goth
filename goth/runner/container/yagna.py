"""Classes to help configure and create `YagnaContainer`s."""

from pathlib import Path
from typing import Any, ClassVar, Dict, Iterator, Optional, Type, TYPE_CHECKING

from docker import DockerClient
from goth.address import (
    HOST_REST_PORT_END,
    HOST_REST_PORT_START,
    YAGNA_REST_PORT,
)
from goth.runner.container import DockerContainer, DockerContainerConfig
from goth.runner.log import LogConfig

if TYPE_CHECKING:
    from goth.runner.probe import Probe  # noqa: F401


class YagnaContainerConfig(DockerContainerConfig):
    """Configuration to be used for creating a new `YagnaContainer`."""

    probe_type: Type["Probe"]
    """Python type of the probe to be instantiated from this config."""

    probe_properties: Dict[str, Any]
    """Additional properties to be set on the probe object."""

    environment: Dict[str, str]
    """Environment variables to be set for this container."""

    key_file: Optional[str]
    """Keyfile to be imported into the yagna id service."""

    privileged_mode: bool
    """If set, docker container will be run in privileged mode."""

    def __init__(
        self,
        name: str,
        probe_type: Type["Probe"],
        probe_properties: Optional[Dict[str, Any]] = None,
        volumes: Optional[Dict[Path, str]] = None,
        log_config: Optional[LogConfig] = None,
        environment: Optional[Dict[str, str]] = None,
        key_file: Optional[str] = None,
        privileged_mode: Optional[bool] = False,
    ):
        super().__init__(name, volumes or {}, log_config)
        self.probe_type = probe_type
        self.probe_properties = probe_properties or {}
        self.environment = environment or {}
        self.key_file = key_file
        self.privileged_mode = privileged_mode


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
            volumes=config.get_volumes_spec(),
            privileged=config.privileged_mode,
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
