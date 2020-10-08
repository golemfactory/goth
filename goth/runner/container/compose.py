"""Module responsible for parsing the docker-compose.yml used in the tests."""
from datetime import datetime
import logging
import os
from pathlib import Path
import subprocess
import queue
import threading
import time
from typing import Dict, Iterator, IO, Optional

from docker import DockerClient
import yaml

from goth.project import DOCKER_DIR
from goth.runner.container.utils import get_container_address
from goth.runner.exceptions import ContainerNotFoundError, CommandError, TimeoutError
from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEventMonitor

logger = logging.getLogger(__name__)

DEFAULT_COMPOSE_FILE = DOCKER_DIR / "docker-compose.yml"
RUN_COMMAND_SLEEP_INTERVAL = 0.1
RUN_COMMAND_DEFAULT_TIMEOUT = 3600


class ComposeNetworkManager:
    """Class which manages a docker-compose network.

    Given the path to a docker-compose.yml file this class can start and stop the
    network, as well as monitor the logs from containers in that network.
    All docker-compose commands are executed in a local shell and not through the
    `DockerClient` used on initialization.
    """

    compose_path: Path
    """Path to compose file to be used with this instance."""

    _docker_client: DockerClient
    """Docker client to be used for high-level Docker API calls."""

    _environment: dict
    """Custom environment variables to be used when running docker-compose commands."""

    _log_monitors: Dict[str, LogEventMonitor]
    """Log monitors for containers running as part of docker-compose."""

    _last_compose_path: Optional[Path] = None
    """Class attribute storing the last compose file used by any manager instance."""

    def __init__(
        self,
        docker_client: DockerClient,
        compose_path: Path,
        environment: dict = {},
    ):
        self.compose_path = compose_path
        self._docker_client = docker_client
        self._environment = environment
        self._log_monitors = {}

    def start_network(self, log_dir: Path, force_build: bool = False) -> None:
        """Start the compose network based on this manager's compose file.

        This step may include (re)building the network's docker images.
        """
        environment = os.environ.update(self._environment)
        command = ["docker-compose", "-f", str(self.compose_path), "up", "-d"]

        if force_build or self.compose_path != ComposeNetworkManager._last_compose_path:
            command.append("--build")

        _run_command(command, env=environment)
        ComposeNetworkManager._last_compose_path = self.compose_path

        self._log_running_containers()
        self._start_log_monitors(log_dir)

    async def stop_network(self):
        """Stop the running compose network, removing its containers."""
        for name, monitor in self._log_monitors.items():
            logger.debug("stopping log monitor. name=%s", name)
            await monitor.stop()

        _run_command(["docker-compose", "-f", str(self.compose_path), "kill"])
        _run_command(["docker-compose", "-f", str(self.compose_path), "rm", "-f"])

    def _get_compose_services(self) -> dict:
        """Return services defined in docker-compose.yml."""
        with self.compose_path.open() as f:
            return yaml.safe_load(f)["services"]

    def _log_running_containers(self):
        for container in self._docker_client.containers.list():
            logger.info(
                "[%-25s] IP address: %-15s image: %s",
                container.name,
                get_container_address(self._docker_client, container.name),
                container.image.tags[0],
            )

    def _start_log_monitors(self, log_dir: Path) -> None:
        for service_name in self._get_compose_services():
            log_config = LogConfig(service_name)
            log_config.base_dir = log_dir
            monitor = LogEventMonitor(log_config)

            containers = self._docker_client.containers.list(
                filters={"name": service_name}
            )
            if not containers:
                raise ContainerNotFoundError(service_name)
            container = containers[0]

            monitor.start(
                container.logs(
                    follow=True,
                    since=datetime.utcnow(),
                    stream=True,
                    timestamps=True,
                )
            )
            self._log_monitors[service_name] = monitor


def _run_command(
    args,
    env: Optional[dict] = None,
    log_prefix: Optional[str] = None,
    timeout: int = RUN_COMMAND_DEFAULT_TIMEOUT,
):
    logger.info("Running local command: %s", " ".join(args))

    if log_prefix is None:
        log_prefix = f"[{args[0]}] "

    starttime = time.time()
    returncode = None

    p = subprocess.Popen(
        args=args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    assert p.stdout  # silence mypy
    out_queue = IOStreamQueue(p.stdout)

    while time.time() < starttime + timeout and returncode is None:
        for line in out_queue.lines():
            logger.debug("%s%s", log_prefix, line.decode("utf-8").rstrip())

        returncode = p.poll()
        if returncode is None:
            time.sleep(RUN_COMMAND_SLEEP_INTERVAL)

        if returncode:
            raise CommandError(
                f"Command exited abnormally. args={args}, returncode={returncode}"
            )

    if returncode is None:
        p.kill()
        raise TimeoutError(
            f"Timeout exceeded while running command. "
            f"args={args}, timeout={timeout}"
        )


class IOStreamQueue:
    """
    Maintains a queue for an output stream - e.g. a launched process' stdout.

    example:
    ```
    p = subprocess.Popen(args=['cmd'], stdout=subprocess.PIPE)
    out_queue = helpers.IOStreamQueue(p.stdout)

    while True:
        for l in out_queue.lines():
            print(l.decode('utf-8'), end='')

        if p.poll() is not None:
            break

        time.sleep(0.1)

    ```
    """

    _output_queue: queue.Queue

    def __init__(self, stream: IO[bytes]):
        def output_queue(s, q):
            for line in iter(s.readline, b""):
                q.put(line)

        self._output_queue = queue.Queue()
        qt = threading.Thread(target=output_queue, args=[stream, self._output_queue])
        qt.daemon = True
        qt.start()

    def lines(self) -> Iterator[bytes]:
        """Yield the lines of the output that have been captured so far."""
        while True:
            try:
                yield self._output_queue.get_nowait()
            except queue.Empty:
                break
