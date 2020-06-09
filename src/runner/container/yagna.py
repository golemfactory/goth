from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

from docker import DockerClient
from src.runner.container import DockerContainer, DockerContainerConfig
from src.runner.log import LogConfig

if TYPE_CHECKING:
    from src.runner.probe import Role


@dataclass(frozen=True)
class YagnaContainerConfig(DockerContainerConfig):
    """ Configuration to be used for creating a new `YagnaContainer`. """

    role: "Role"
    """ Role this container has in a test scenario """

    log_config: Optional[LogConfig] = None
    """ Optional custom logging config to be used for this container """

    environment: Dict[str, str] = field(default_factory=dict)
    """ Environment variables to be set for this container """


class YagnaContainer(DockerContainer):
    BUS_PORT = 6010
    HTTP_PORT = 6000
    COMMAND = ["service", "run", "-d", "/"]
    ENTRYPOINT = "/usr/bin/yagna"
    IMAGE = "yagna"

    # Keeps track of assigned ports on the Docker host
    _port_offset = 0

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: Optional[LogConfig] = None,
        assets_path: Optional[Path] = None,
        **kwargs,
    ):
        self.environment = config.environment
        self.ports = {
            YagnaContainer.HTTP_PORT: YagnaContainer.host_http_port(),
            YagnaContainer.BUS_PORT: YagnaContainer.host_bus_port(),
        }
        YagnaContainer._port_offset += 1

        super().__init__(
            client=client,
            command=self.COMMAND,
            entrypoint=self.ENTRYPOINT,
            environment=self.environment,
            image=self.IMAGE,
            log_config=log_config,
            name=config.name,
            ports=self.ports,
            volumes=config.get_volumes_spec(assets_path) if assets_path else {},
            **kwargs,
        )

    @classmethod
    def host_http_port(cls):
        return cls.HTTP_PORT + cls._port_offset

    @classmethod
    def host_bus_port(cls):
        return cls.BUS_PORT + cls._port_offset
