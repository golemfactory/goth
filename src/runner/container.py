from dataclasses import dataclass, field
from enum import Enum
from string import Template
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from docker import DockerClient
from docker.models.containers import Container
from transitions import Machine

from src.runner.log import get_file_logger, LogBuffer

if TYPE_CHECKING:
    from src.runner.probe import Role


class State(Enum):
    """ Represents states that a Docker container may be in. """

    created = 0
    started = 1
    stopped = 2
    removed = 3


class DockerContainer:
    """ A wrapper around `Container` which includes a state machine (from `transitions`)
        to keep track of a container's lifecycle. """

    DEFAULT_NETWORK = "docker_default"

    command: List[str]
    """ Arguments passed to this container's `command` """

    entrypoint: str
    """ The binary to be run by this container once started """

    image: str
    """ Name of the image to be used for creating this container """

    logs: Optional[LogBuffer]
    """ Log buffer for the logs from this container's `entrypoint` """

    name: str
    """ Name to be assigned to this container """

    network: str
    """ Name of the Docker network to be joined once the container is started """

    # This section lists the members which will be added at runtime by `transitions`
    state: State
    """ Current state of this container """

    stop: Callable
    """ Stop a running container. Internally, this calls `Container.stop` with any kwargs
        passed here being forwarded to that function. """
    start: Callable
    """ Start a container which is either created or stopped.
        Internally, this calls `Container.start` with any kwargs passed here being
        forwarded to that function. """
    remove: Callable
    """ Remove a container. This puts this `DockerContainer` in its final state `State.removed`.
        Internally, this calls `Container.remove` with any kwargs passed here being
        forwarded to that function. """

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

        # Initialise the state machine and define allowed transitions
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
        """ Proxy to `Container.exec_run`. """
        return self._container.exec_run(*args, **kwargs)


class YagnaContainer(DockerContainer):
    BUS_PORT = 6010
    HTTP_PORT = 6000
    COMMAND = ["service", "run", "-d", "/"]
    ENTRYPOINT = "/usr/bin/yagna"
    IMAGE = "yagna"

    # Keeps track of assigned ports on the Docker host
    _port_offset = 0

    @dataclass
    class Config:
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

    def __init__(self, client: DockerClient, config: Config):
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
        )

    @classmethod
    def host_http_port(cls):
        return cls.HTTP_PORT + cls._port_offset

    @classmethod
    def host_bus_port(cls):
        return cls.BUS_PORT + cls._port_offset
