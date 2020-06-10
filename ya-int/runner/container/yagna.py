from dataclasses import dataclass, field
from string import Template
from typing import Dict, TYPE_CHECKING

from docker import DockerClient

from runner.container import DockerContainer

if TYPE_CHECKING:
    from runner.probe import Role


@dataclass
class YagnaContainerConfig:
    """ Configuration to be used for creating a new `YagnaContainer`. """

    name: str
    """ Name to be used for this container, must be unique """

    role: "Role"

    assets_path: str = ""
    """ Path to the assets directory. This will be used in templates from `volumes` """

    environment: Dict[str, str] = field(default_factory=dict)
    """ Environment variables to be set for this container """

    volumes: Dict[Template, str] = field(default_factory=dict)
    """ Volumes to be mounted in the container. Keys are paths on the host machine,
        represented by `Template`s. These templates may include `assets_path`
        as a placeholder to be used for substitution.  The values are container
        paths to be used as mount points. """


class YagnaContainer(DockerContainer):
    BUS_PORT = 6010
    HTTP_PORT = 6000
    COMMAND = ["service", "run", "-d", "/"]
    ENTRYPOINT = "/usr/bin/yagna"
    IMAGE = "yagna"

    # Keeps track of assigned ports on the Docker host
    _port_offset = 0

    def __init__(self, client: DockerClient, config: YagnaContainerConfig, **kwargs):
        self.environment = config.environment
        self.ports = {
            YagnaContainer.HTTP_PORT: YagnaContainer.host_http_port(),
            YagnaContainer.BUS_PORT: YagnaContainer.host_bus_port(),
        }
        self.volumes: Dict[str, dict] = {}
        for host_template, mount_path in config.volumes.items():
            host_path = host_template.substitute(assets_path=config.assets_path)
            self.volumes[host_path] = {"bind": mount_path, "mode": "ro"}

        YagnaContainer._port_offset += 1

        super().__init__(
            client,
            self.COMMAND,
            self.ENTRYPOINT,
            self.IMAGE,
            config.name,
            environment=self.environment,
            ports=self.ports,
            volumes=self.volumes,
            **kwargs,
        )

    @classmethod
    def host_http_port(cls):
        return cls.HTTP_PORT + cls._port_offset

    @classmethod
    def host_bus_port(cls):
        return cls.BUS_PORT + cls._port_offset
