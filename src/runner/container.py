from enum import Enum
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from docker import DockerClient
from docker.models.containers import Container
from transitions import Machine

from src.runner.log import get_file_logger, LogBuffer

if TYPE_CHECKING:
    from src.runner.probe import NodeConfig


class State(Enum):
    created = 0
    started = 1
    stopped = 2
    removed = 3


class DockerContainer:
    DEFAULT_NETWORK = "docker_default"

    command: List[str]
    entrypoint: str
    image: str
    logs: Optional[LogBuffer]
    name: str
    network: str

    state: State
    stop: Callable
    start: Callable
    remove: Callable

    _client: DockerClient
    _container: Container

    def __init__(
        self,
        client: DockerClient,
        command: List[str],
        entrypoint: str,
        image: str,
        name: str,
        network: str = DEFAULT_NETWORK,
        **kwargs,
    ):
        self._client = client
        self.command = command
        self.entrypoint = entrypoint
        self.image = image
        self.name = name
        self.network = network

        self._container = self._client.containers.create(
            self.image,
            entrypoint=self.entrypoint,
            command=self.command,
            detach=True,
            name=self.name,
            network=self.network,
            **kwargs,
        )

        self.machine = Machine(
            self,
            states=State,
            transitions=[
                {
                    "trigger": "start",
                    "source": [State.created, State.stopped],
                    "dest": State.started,
                    "before": self._container.start,
                },
                {
                    "trigger": "stop",
                    "source": State.started,
                    "dest": State.stopped,
                    "before": self._container.stop,
                },
                {
                    "trigger": "remove",
                    "source": "*",
                    "dest": State.removed,
                    "before": self._container.remove,
                },
            ],
            initial=State.created,
            auto_transitions=False,
        )

        self.logs = LogBuffer(
            self._container.logs(stream=True, follow=True), get_file_logger(self.name)
        )

    def exec_run(self, *args, **kwargs):
        return self._container.exec_run(*args, **kwargs)


class YagnaContainer(DockerContainer):
    BUS_PORT = 6010
    HTTP_PORT = 6000
    COMMAND = ["service", "run", "-d", "/"]
    ENTRYPOINT = "/usr/bin/yagna"
    IMAGE = "yagna"

    # Keeps track of assigned ports on the Docker host
    port_offset = 0

    def __init__(self, client: DockerClient, config: "NodeConfig"):
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

        super().__init__(
            client,
            self.COMMAND,
            self.ENTRYPOINT,
            self.IMAGE,
            config.name,
            environment=self.environment,
            ports=self.ports,
            volumes=self.volumes,
        )

    @classmethod
    def host_http_port(cls):
        return cls.HTTP_PORT + cls.port_offset

    @classmethod
    def host_bus_port(cls):
        return cls.BUS_PORT + cls.port_offset
