"""Module responsible for parsing the docker-compose.yml used in the tests."""
import asyncio
from datetime import datetime
import logging
import os
from pathlib import Path
import subprocess
from typing import ClassVar, Dict, Optional, Sequence

from docker import DockerClient
import yaml

from goth.project import DOCKER_DIR
from goth.runner.container import DockerContainer
from goth.runner.container.utils import get_container_address
from goth.runner.exceptions import ContainerNotFoundError, CommandError
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

    _environment: Optional[dict]
    """Custom environment variables to be used when running docker-compose commands."""

    _log_monitors: Dict[str, LogEventMonitor]
    """Log monitors for containers running as part of docker-compose."""

    _last_compose_path: ClassVar[Optional[Path]] = None
    """Class attribute storing the last compose file used by any manager instance."""

    _network_gateway_address: str
    """IP address of the gateway for the docker network."""

    def __init__(
        self,
        docker_client: DockerClient,
        compose_path: Path,
        environment: Optional[dict] = None,
    ):
        self.compose_path = compose_path.resolve()
        self._docker_client = docker_client
        self._environment = environment
        self._log_monitors = {}
        self._network_gateway_address = ""

    async def start_network(self, log_dir: Path, force_build: bool = False) -> None:
        """Start the compose network based on this manager's compose file.

        This step may include (re)building the network's docker images.
        """
        environment = (
            {**os.environ, **self._environment} if self._environment else {**os.environ}
        )
        command = ["docker-compose", "-f", str(self.compose_path), "up", "-d"]

        if force_build or self.compose_path != ComposeNetworkManager._last_compose_path:
            command.append("--build")

        await _run_command(command, env=environment)
        ComposeNetworkManager._last_compose_path = self.compose_path

        self._log_running_containers()
        self._start_log_monitors(log_dir)

    async def stop_network(self):
        """Stop the running compose network, removing its containers."""
        for name, monitor in self._log_monitors.items():
            logger.debug("stopping log monitor. name=%s", name)
            await monitor.stop()

        await _run_command(["docker-compose", "-f", str(self.compose_path), "kill"])
        await _run_command(["docker-compose", "-f", str(self.compose_path), "rm", "-f"])

    def _get_compose_services(self) -> dict:
        """Return services defined in docker-compose.yml."""
        with self.compose_path.open() as f:
            return yaml.safe_load(f)["services"]

    @property
    def network_gateway_address(self) -> str:
        """Get the IP address of the gateway for the docker network."""

        if not self._network_gateway_address:
            # TODO: parse the docker compose file to get network name,
            # use the default name as fallback
            network_name = DockerContainer.DEFAULT_NETWORK
            network = self._docker_client.networks.get(network_name)
            network_cfg = network.attrs["IPAM"]["Config"][0]
            if "Gateway" in network_cfg:
                self._network_gateway_address = network_cfg["Gateway"]
            else:
                # Use the "subnet" with the last element replaced by "1",
                # e.g. for subnet "172.19.0.0/16" return "172.19.0.1".
                # Not sure if it's totally correct though...
                subnet = network_cfg["Subnet"]
                segments = subnet.split(".")
                assert len(segments) == 4
                segments[3] = "1"
                self._network_gateway_address = ".".join(segments)

        return self._network_gateway_address

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
                    follow=True, since=datetime.utcnow(), stream=True, timestamps=True
                )
            )
            self._log_monitors[service_name] = monitor


async def _run_command(
    args: Sequence[str],
    env: Optional[dict] = None,
    log_prefix: Optional[str] = None,
    timeout: int = RUN_COMMAND_DEFAULT_TIMEOUT,
):
    logger.info("Running local command: %s", " ".join(args))

    if log_prefix is None:
        log_prefix = f"[{args[0]}] "

    p = subprocess.Popen(
        args=args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    async def _read_output():
        for line in p.stdout:
            logger.debug("%s%s", log_prefix, line.decode("utf-8").rstrip())

        return_code = p.poll()
        if return_code:
            raise CommandError(
                f"Command exited abnormally. args={args}, return_code={return_code}"
            )
        else:
            await asyncio.sleep(RUN_COMMAND_SLEEP_INTERVAL)

    await asyncio.wait_for(_read_output(), timeout=timeout)
