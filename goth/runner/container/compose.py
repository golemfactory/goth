"""Module responsible for parsing the docker-compose.yml used in the tests."""
import contextlib
from dataclasses import dataclass
from datetime import datetime
import logging
import os
from pathlib import Path
import time
from typing import AsyncIterator, ClassVar, Dict, List, Optional

from docker import DockerClient
from docker.models.networks import Network
import yaml

from goth.runner.container import DockerContainer
from goth.runner.container.build import (
    build_proxy_image,
    build_yagna_image,
    YagnaBuildEnvironment,
)
from goth.runner.container.utils import get_container_network_info
from goth.runner.exceptions import ContainerNotFoundError, CommandError
from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEventMonitor
from goth.runner.process import run_command

logger = logging.getLogger(__name__)

CONTAINER_READY_TIMEOUT = 60  # in seconds
DEFAULT_COMPOSE_FILE = "docker-compose.yml"


@dataclass
class ComposeConfig:
    """Configuration class for `ComposeNetworkManager` instances."""

    build_env: YagnaBuildEnvironment
    """Build environment for building yagna images."""

    file_path: Path
    """Path to the docker-compose.yml file to be used."""

    log_patterns: Dict[str, str]
    """Mapping between service names and regex patterns to look for in their logs.

    The `ComposeNetworkManager` being configured by this object will use the entries
    from this dict to perform ready checks on services. For each service (key)
    the manager will wait for a log line to match the regex pattern (value).
    """


@dataclass
class ContainerInfo:
    """Info on a Docker container started by Docker compose."""

    address: str
    """The container's IP address in the Docker network"""

    aliases: List[str]
    """Container aliases in the Docker network"""

    image: str
    """The container's image name"""


class ComposeNetworkManager:
    """Class which manages a docker-compose network.

    Given the path to a docker-compose.yml file this class can start and stop the
    network, as well as monitor the logs from containers in that network.
    All docker-compose commands are executed in a local shell and not through the
    `DockerClient` used on initialization.
    """

    config: ComposeConfig
    """Configuration for this manager instance."""

    _docker_client: DockerClient
    """Docker client to be used for high-level Docker API calls."""

    _last_compose_path: ClassVar[Optional[Path]] = None
    """Class attribute storing the last compose file used by any manager instance."""

    _log_monitors: Dict[str, LogEventMonitor]
    """Log monitors for containers running as part of docker-compose."""

    _network_gateway_address: str
    """IP address of the gateway for the docker network."""

    def __init__(
        self,
        docker_client: DockerClient,
        config: ComposeConfig,
    ):
        self.config = config
        self.config.file_path = config.file_path.resolve()
        self._docker_client = docker_client
        self._log_monitors = {}
        self._network_gateway_address = ""

    async def start_network(
        self, log_dir: Path, force_build: bool = False
    ) -> Dict[str, ContainerInfo]:
        """Start the compose network based on this manager's compose file.

        Returns information on containers started in the compose network.
        This step may include (re)building the network's docker images.
        """
        # Stop the network in case it's already running (e.g. from a previous test)
        await self.stop_network()

        command = ["docker-compose", "-f", str(self.config.file_path), "up", "-d"]

        await build_yagna_image(self.config.build_env)
        await build_proxy_image(self.config.build_env.docker_dir)

        if force_build or self.config.file_path != ComposeNetworkManager._last_compose_path:
            command.append("--build")

        await run_command(command, env={**os.environ})
        ComposeNetworkManager._last_compose_path = self.config.file_path

        self._start_log_monitors(log_dir)
        await self._wait_for_containers()
        container_infos = self._get_running_containers()
        for name, info in container_infos.items():
            logger.info("[%-25s] IP address: %-15s image: %s", name, info.address, info.image)
        return container_infos

    async def _wait_for_containers(self) -> None:
        logger.info("Waiting for compose containers to be ready")
        for name, pattern in self.config.log_patterns.items():
            monitor = self._log_monitors.get(name)
            if not monitor:
                raise RuntimeError(f"No log monitor found for container: {name}")

            logger.debug(
                "Waiting for container to be ready. name=%s, log_pattern=%s",
                name,
                pattern,
            )
            await monitor.wait_for_entry(pattern, timeout=CONTAINER_READY_TIMEOUT)
        logger.info("Compose network ready")

    def _disconnect_containers(self, excluded_containers: List[str]) -> None:
        """Disconnect containers from the default Docker compose network.

        This corresponds to executing the command
        >>> docker network disconnect -f DEFAULT_NETWORK CONTAINER_NAME
        for each container.

        All containers except those with names in `excluded_containers` are
        disconnected.
        """
        networks = self._docker_client.networks.list(names=[DockerContainer.DEFAULT_NETWORK])
        if networks:
            compose_network: Network = networks[0]
            compose_network.reload()
            connected_containers = [c["Name"] for c in compose_network.attrs["Containers"].values()]
            yagna_containers = [
                name for name in connected_containers if name not in excluded_containers
            ]
            for container in yagna_containers:
                logger.info(
                    "Disconnecting container %s from network %s...",
                    container,
                    DockerContainer.DEFAULT_NETWORK,
                )
                compose_network.disconnect(container, force=True)

    async def stop_network(self, compose_containers: Optional[List[str]] = None):
        """Stop the running compose network, removing its containers.

        Before the network is stopped, all yagna containers need to be disconnected,
        due to https://github.com/moby/moby/issues/23302.

        To avoid explicitly disconnecting some containers -- for example, the ones
        started by `docker-compose` itself that will be disconnected by
        `docker-compose down` -- pass their names in `compose_containers`.
        """

        for name, monitor in self._log_monitors.items():
            logger.debug("stopping log monitor. name=%s", name)
            await monitor.stop()

        self._disconnect_containers(compose_containers or [])

        compose_down_cmd = [
            "docker-compose",
            "-f",
            str(self.config.file_path),
            "down",
            "-t",
            "0",
            "--remove-orphans",
        ]
        try:
            await run_command(compose_down_cmd)
        except CommandError as e:
            logger.warn(f"docker-compose down error: {e}, retrying in 300s")
            time.sleep(300)
            await run_command(compose_down_cmd)

    def _get_compose_services(self) -> dict:
        """Return services defined in docker-compose.yml."""
        with self.config.file_path.open() as f:
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

    def _get_running_containers(self) -> Dict[str, ContainerInfo]:
        info = {}
        for container in self._docker_client.containers.list():
            address, aliases = get_container_network_info(self._docker_client, container.name)
            image = container.image.tags[0]
            info[container.name] = ContainerInfo(address, aliases, image)
        return info

    def _start_log_monitors(self, log_dir: Path) -> None:
        for service_name in self._get_compose_services():
            log_config = LogConfig(service_name)
            log_config.base_dir = log_dir
            monitor = LogEventMonitor(service_name, log_config)

            containers = self._docker_client.containers.list(filters={"name": service_name})
            if not containers:
                raise ContainerNotFoundError(service_name)
            container = containers[0]

            monitor.start(
                container.logs(follow=True, since=datetime.utcnow(), stream=True, timestamps=True)
            )
            self._log_monitors[service_name] = monitor


@contextlib.asynccontextmanager
async def run_compose_network(
    compose_manager: ComposeNetworkManager, log_dir: Path, force_build: bool = False
) -> AsyncIterator[Dict[str, ContainerInfo]]:
    """Implement AsyncContextManager for starting/stopping docker compose network.

    Yields information on containers started in the compose network.
    """

    compose_containers = []
    try:
        logger.debug("Starting compose network. log_dir=%s, force_build=%s", log_dir, force_build)
        containers = await compose_manager.start_network(log_dir, force_build)
        compose_containers = list(containers.keys())
        yield containers
    finally:
        logger.debug("Stopping compose network")
        await compose_manager.stop_network(compose_containers)
