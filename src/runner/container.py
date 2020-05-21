from typing import Dict, List, Optional, TYPE_CHECKING

from docker import DockerClient
from docker.models.containers import Container

from src.runner.log import get_file_logger, LogBuffer

if TYPE_CHECKING:
    from src.runner.probe import NodeConfig


class DockerContainer:

    command: List[str]
    entrypoint: str
    image: str
    name: str
    network: str

    _client: DockerClient
    _container: Optional[Container]

    def __init__(
        self,
        client: DockerClient,
        command: List[str],
        entrypoint: str,
        image: str,
        name: str,
        network: str = "docker_default",
    ):
        self._client = client
        self.command = command
        self.entrypoint = entrypoint
        self.image = image
        self.name = name
        self.network = network

    def run(self, **kwargs) -> LogBuffer:
        self._container = self._client.containers.run(
            self.image,
            entrypoint=self.entrypoint,
            command=self.command,
            detach=True,
            name=self.name,
            network=self.network,
            **kwargs,
        )

        return LogBuffer(
            self._container.logs(stream=True, follow=True), get_file_logger(self.name)
        )

    def exec_run(self, *args, **kwargs):
        return self._container.exec_run(*args, **kwargs)

    def remove(self, **kwargs):
        return self._container.remove(**kwargs)


class YagnaContainer(DockerContainer):
    BUS_PORT = 6010
    HTTP_PORT = 6000
    COMMAND = ["service", "run", "-d", "/"]
    ENTRYPOINT = "/usr/bin/yagna"
    IMAGE_NAME = "yagna"

    # Keeps track of assigned ports on the Docker host
    port_offset = 0

    def __init__(self, client: DockerClient, config: "NodeConfig"):
        super().__init__(
            client, self.COMMAND, self.ENTRYPOINT, self.IMAGE_NAME, config.name
        )

        self.environment = []
        for key, value in config.environment.items():
            self.environment.append(f"{key}={value}")
        self.ports = {
            YagnaContainer.HTTP_PORT: YagnaContainer.host_http_port(),
            YagnaContainer.BUS_PORT: YagnaContainer.host_bus_port(),
        }
        self.volumes: Dict[str, dict] = {}
        for host_template, mount_path in config.volumes.items():
            host_path = host_template.substitute(assets_path=config.assets_path)
            self.volumes[host_path] = {"bind": mount_path, "mode": "ro"}

        YagnaContainer.port_offset += 1

    @classmethod
    def host_http_port(cls):
        return cls.HTTP_PORT + cls.port_offset

    @classmethod
    def host_bus_port(cls):
        return cls.BUS_PORT + cls.port_offset

    def run(self, **kwargs) -> LogBuffer:
        return super().run(
            environment=self.environment,
            ports=self.ports,
            volumes=self.volumes,
            **kwargs,
        )
