"""Module responsible for parsing the docker-compose.yml used in the tests."""
from datetime import datetime
import logging
import os
from pathlib import Path
import subprocess
import time
from typing import Dict, Optional

from docker import DockerClient
import yaml

from goth.helpers import IOStreamQueue
from goth.runner.exceptions import ContainerNotFoundError, CommandError, TimeoutError
from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEventMonitor

logger = logging.getLogger(__name__)

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

    def start_network(self, log_dir: Path) -> None:
        """Start the compose network based on this manager's compose file.

        This step may include (re)building the network docker images.
        """
        env = os.environ.update(self._environment)

        # TODO Cache last used compose file path
        self._run_command(
            ["docker-compose", "-f", str(self.compose_path), "up", "-d", "--build"],
            env=env,
        )

        self._start_log_monitors(log_dir)

    async def stop_network(self):
        """Stop the running compose network, removing its containers."""
        for name, monitor in self._log_monitors.items():
            logger.debug("stopping log monitor. name=%s", name)
            await monitor.stop()

        self._run_command(["docker-compose", "-f", str(self.compose_path), "kill"])
        self._run_command(["docker-compose", "-f", str(self.compose_path), "rm", "-f"])

    def _get_compose_services(self) -> dict:
        """Return services defined in docker-compose.yml."""
        with self.compose_path.open() as f:
            return yaml.safe_load(f)["services"]

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

    @staticmethod
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
                logger.info("%s%s", log_prefix, line.decode("utf-8").rstrip())

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
