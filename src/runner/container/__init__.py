from enum import Enum
from typing import Callable, List, Optional

from docker import DockerClient
from docker.models.containers import Container
from transitions import Machine

from src.runner.log import get_file_logger, LogBuffer


class State(Enum):
    """ Represents states that a Docker container may be in. """

    created = 0
    running = 1
    restarting = 2
    removing = 3
    paused = 4
    exited = 5
    dead = 6


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
    stop: Callable
    """ Stop a running container. Internally, this calls `Container.stop` with any kwargs
        passed here being forwarded to that function. """

    start: Callable
    """ Start a container which is either created or stopped.
        Internally, this calls `Container.start` with any kwargs passed here being
        forwarded to that function. """

    remove: Callable
    """ Remove a container. This puts this `DockerContainer` in its final state
        `State.dead`. Internally, this calls `Container.remove` with any kwargs
        passed here being forwarded to that function. """

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
        network: str = DEFAULT_NETWORK,
        log_to_file: bool = True,
        **kwargs,
    ):
        self._client = client
        self.command = command
        self.entrypoint = entrypoint
        self.image = image
        self.name = name
        self.network = network
        self.log_to_file = log_to_file

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
            ],
            initial=State.created,
            model_attribute="_state",  # name of the field under which state is stored
            prepare_event="_update_state",  # function to run before each transition
            auto_transitions=False,  # do not generate transition functions
        )

    @property
    def state(self) -> State:
        """ Current state of this container as reported by the Docker daemon """
        self._update_state()
        return self._state

    def exec_run(self, *args, **kwargs):
        """ Proxy to `Container.exec_run`. """
        return self._container.exec_run(*args, **kwargs)

    def _start(self, **kwargs):
        self._container.start(**kwargs)
        if self.log_to_file:
            self.logs = LogBuffer(
                self._container.logs(stream=True, follow=True),
                get_file_logger(self.name),
            )

    def _update_state(self, *_args, **_kwargs):
        """ Update the state machine based on data obtained from the Docker daemon
            by reloading the inner `Container` object. """
        self._container.reload()
        self.machine.set_state(State[self._container.status])
