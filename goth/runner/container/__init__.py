"""Classes and utilties to manage docker Containers."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

from docker import DockerClient
from docker.models.containers import Container
from transitions import Machine

from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEventMonitor


@dataclass
class DockerContainerConfig:
    """Configuration to be used for creating a new docker container."""

    name: str
    """Name to be used for this container, must be unique."""

    volumes: Dict[Path, str] = field(default_factory=dict)
    """Volumes to be mounted in the container.

    Keys in this dictionary are paths on the host machine. The values
    are container paths to be used as mount points.
    """

    log_config: Optional[LogConfig] = None
    """Optional custom logging config to be used for this container."""

    privileged_mode: bool = False
    """If set, docker container will be run in privileged mode."""


class State(Enum):
    """Represents states that a Docker container may be in."""

    created = 0
    running = 1
    restarting = 2
    removing = 3
    paused = 4
    exited = 5
    dead = 6


class DockerContainer:
    """A wrapper around `Container`.

    Includes a state machine (from `transitions`) to keep track of a container's
    lifecycle.
    """

    DEFAULT_NETWORK = "docker_default"

    command: List[str]
    """Arguments passed to this container's `command`."""

    entrypoint: str
    """The binary to be run by this container once started."""

    image: str
    """Name of the image to be used for creating this container."""

    logs: Optional[LogEventMonitor]
    """Log buffer for the logs from this container's `entrypoint`."""

    name: str
    """Name to be assigned to this container."""

    network: str
    """Name of the Docker network to be joined once the container is started."""

    # This section lists the members which will be added at runtime by `transitions`
    stop: Callable
    """Stop a running container.

    Internally, this calls `Container.stop` with any kwargs passed here being forwarded
    to that function.
    """

    start: Callable
    """ Start a container which is either created or stopped.

    Internally, this calls `Container.start` with any kwargs passed here being forwarded
    to that function.
    """

    remove: Callable
    """Remove a container.

    This puts this `DockerContainer` in its final state `State.dead`. Internally, this
    calls `Container.remove` with any kwargs passed here being forwarded to that
    function.
    """

    restart: Callable
    """Restart a container.

    Internally, this calls `Container.restart` with any kwargs passed here being
    forwarded to that function.
    """

    _client: DockerClient
    _container: Container
    _state: State

    def __init__(
        self,
        client: DockerClient,
        command: List[str],
        entrypoint: str,
        image: str,
        name: str,
        log_config: Optional[LogConfig] = None,
        network: str = DEFAULT_NETWORK,
        **kwargs,
    ):
        self._client = client
        self.command = command
        self.entrypoint = entrypoint
        self.image = image
        self.name = name
        self.network = network
        self.log_config = log_config
        self.logs = None
        if self.log_config:
            self.logs = LogEventMonitor(self.name, self.log_config)

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
        self._state = State.created
        self.machine = Machine(
            self,
            states=State,
            transitions=[
                {
                    "trigger": "start",
                    "source": [State.created, State.exited],
                    "dest": State.running,
                    "before": self._start,
                },
                {
                    "trigger": "stop",
                    "source": [State.running, State.paused, State.restarting],
                    "dest": State.exited,
                    "before": self._container.stop,
                },
                {
                    "trigger": "remove",
                    "source": "*",
                    "dest": State.dead,
                    "before": self._container.remove,
                },
                {
                    "trigger": "restart",
                    "source": [State.running, State.paused, State.exited],
                    "dest": State.running,
                    "before": self._restart,
                },
            ],
            initial=State.created,
            model_attribute="_state",  # name of the field under which state is stored
            prepare_event="_update_state",  # function to run before each transition
            auto_transitions=False,  # do not generate transition functions
        )

    @property
    def state(self) -> State:
        """State of this container as reported by the Docker daemon."""
        self._update_state()
        return self._state

    def exec_run(self, *args, **kwargs):
        """Proxy to `Container.exec_run`."""
        return self._container.exec_run(*args, **kwargs)

    def _start(self, **kwargs):
        """Start the container."""
        self._container.start(**kwargs)
        if self.logs:
            self.logs.start(self._container.logs(stream=True, follow=True))

    def _restart(self):
        """Restart the container."""
        self._container.restart()
        if self.logs:
            # using naive datetime object as `since` argument deliberately
            # see: https://github.com/docker/docker-py/issues/2712
            self.logs.update_stream(
                self._container.logs(stream=True, follow=True, since=datetime.utcnow())
            )

    def _update_state(self, *_args, **_kwargs):
        """Update the state machine.

        Data is obtained from the Docker daemon by reloading the inner `Container`
        object.
        """

        self._container.reload()
        self.machine.set_state(State[self._container.status])
