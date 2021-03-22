"""Classes and helpers for managing Probes."""

import abc
import asyncio
import contextlib
import copy
import logging
from pathlib import Path
from typing import (
    AsyncIterator,
    Dict,
    Iterator,
    Optional,
    Tuple,
    TYPE_CHECKING,
)

from docker import DockerClient

from goth.address import (
    YAGNA_BUS_URL,
    YAGNA_REST_PORT,
    YAGNA_REST_URL,
)

from goth import gftp
from goth.node import DEFAULT_SUBNET
from goth.runner.agent import AgentMixin
from goth.runner.api_client import ApiClientMixin
from goth.runner.cli import Cli, YagnaDockerCli
from goth.runner.container.utils import get_container_address
from goth.runner.container.yagna import (
    YagnaContainer,
    YagnaContainerConfig,
    PAYMENT_MOUNT_PATH,
)
from goth.runner.exceptions import KeyAlreadyExistsError
from goth.runner.log import LogConfig, monitored_logger
from goth.runner.log_monitor import PatternMatchingWaitableMonitor
from goth.runner import process


if TYPE_CHECKING:
    from goth.runner import Runner

logger = logging.getLogger(__name__)


class ProbeLoggingAdapter(logging.LoggerAdapter):
    """Adds probe name information to log messages."""

    EXTRA_PROBE_NAME = "probe_name"

    def process(self, msg, kwargs):
        """Process the log message."""
        return "[%s] %s" % (self.extra[self.EXTRA_PROBE_NAME], msg), kwargs


class Probe(abc.ABC):
    """Provides a unified interface for interacting with and testing a single Yagna node.

    This interface consists of several independent modules which may be extended
    in subclasses (see `ProviderProbe` and `RequestorProbe`).
    """

    runner: "Runner"
    """A runner that created this probe."""

    cli: YagnaDockerCli
    """A module which enables calling the Yagna CLI on the daemon being tested."""

    container: YagnaContainer
    """A module which handles the lifecycle of the daemon's Docker container."""

    ip_address: Optional[str] = None
    """An IP address of the daemon's container in the Docker network."""

    _docker_client: DockerClient
    """A docker client used to create the deamon's container."""

    _gftp_script_dir: Path
    """Directory containing the `gftp` proxy script.

    This script forwards JSON RPC requests to the `gftp` binary running in the docker
    container managed by this probe, and returns responses from the binary.
    """

    _yagna_config: YagnaContainerConfig
    """Config object used for setting up the Yagna node for this probe."""

    def __init__(
        self,
        runner: "Runner",
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
    ):
        self.runner = runner
        self._docker_client = client
        self._logger = ProbeLoggingAdapter(
            logger, {ProbeLoggingAdapter.EXTRA_PROBE_NAME: config.name}
        )
        config = self._setup_gftp_proxy(config)
        self.container = YagnaContainer(client, config, log_config)
        self.cli = Cli(self.container).yagna
        self._yagna_config = config

    def __str__(self):
        return self.name

    @property
    def address(self) -> Optional[str]:
        """Return address from id marked as default."""
        identity = self.cli.id_show()
        return identity.address if identity else None

    @property
    def app_key(self) -> Optional[str]:
        """Return first app key on the list."""
        keys = self.cli.app_key_list()
        return keys[0].key if keys else None

    @property
    def name(self) -> str:
        """Name of the container."""
        return self.container.name

    def _setup_gftp_proxy(self, config: YagnaContainerConfig) -> YagnaContainerConfig:
        """Create a proxy script and a dir for exchanging files with the container."""

        self._gftp_script_dir, gftp_volume_dir = gftp.create_gftp_dirs(config.name)
        self._logger.info("Created gftp script at %s", self._gftp_script_dir)

        new_config = copy.deepcopy(config)
        new_config.volumes[gftp_volume_dir] = gftp.CONTAINER_MOUNT_POINT
        self._logger.info(
            "Gftp volume %s will be mounted at %s in the container",
            gftp_volume_dir,
            gftp.CONTAINER_MOUNT_POINT,
        )

        return new_config

    async def start(self) -> None:
        """Start the probe.

        This method is extended in subclasses and mixins.
        """

        await self._start_container()

    async def stop(self):
        """
        Stop the probe, removing the Docker container of the daemon being tested.

        Once stopped, a probe cannot be restarted.
        """
        self._logger.info("Stopping probe")
        if self.container.logs:
            await self.container.logs.stop()

    def remove(self) -> None:
        """Remove the underlying container."""
        if self.container:
            self.container.remove(force=True)
            self._logger.debug("Container removed")

    async def _start_container(self) -> None:
        """
        Start the probe's Docker container.

        Performs all necessary steps to make the daemon ready for testing
        (e.g. creating the default app key).
        """
        self.container.start()

        # Wait until the daemon is ready to create an app key.
        self._logger.info("Waiting for connection to ya-sb-router")
        if self.container.logs:
            await self.container.logs.wait_for_entry(
                ".*connected with server: ya-sb-router.*", timeout=30
            )
        await self.create_app_key()

        self._logger.info("Waiting for yagna REST API to be listening")
        if self.container.logs:
            await self.container.logs.wait_for_entry(
                "Starting .* service on .*.", timeout=30
            )

        # Obtain the IP address of the container
        self.ip_address = get_container_address(
            self._docker_client, self.container.name
        )
        self._logger.info("IP address: %s", self.ip_address)

    async def create_app_key(self, key_name: str = "test_key") -> str:
        """Attempt to create a new app key on the Yagna daemon.

        The key name can be specified via `key_name` parameter.
        Return the key as string.

        When `self.key_file` is set, this method also:
        - creates ID based on `self.key_file`
        - sets this new ID as default
        - restarts the container ( https://github.com/golemfactory/yagna/issues/458 )
        """
        address = None
        if self._yagna_config.payment_id:
            key_name = self._yagna_config.payment_id.key_file.name
            key_file: str = str(PAYMENT_MOUNT_PATH / key_name)
            self._logger.debug("create_id(alias=%s, key_file=%s", key_name, key_file)
            try:
                db_id = self.cli.id_create(alias=key_name, key_file=key_file)
                address = db_id.address
                self._logger.debug("create_id. alias=%s, address=%s", db_id, address)
            except KeyAlreadyExistsError as e:
                logger.critical("Id already exists : (%r)", e)
                raise
            db_id = self.cli.id_update(address, set_default=True)
            self._logger.debug("update_id. result=%r", db_id)
            self.container.restart()
            await asyncio.sleep(5)
        try:
            key = self.cli.app_key_create(key_name)
            self._logger.debug("create_app_key. key_name=%s, key=%s", key_name, key)
        except KeyAlreadyExistsError:
            app_key = next(
                filter(lambda k: k.name == key_name, self.cli.app_key_list())
            )
            key = app_key.key
        return key

    def set_agent_env_vars(self, env: Dict[str, str]) -> None:
        """Add vars needed to talk to the daemon in this probe's container to `env`."""

        if not self.app_key:
            raise AttributeError("Yagna application key is not set yet")
        path_var = env.get("PATH")
        env.update(
            {
                "YAGNA_APPKEY": self.app_key,
                "YAGNA_API_URL": YAGNA_REST_URL.substitute(host=self.ip_address),
                "GSB_URL": YAGNA_BUS_URL.substitute(host=self.ip_address),
                "PATH": f"{self._gftp_script_dir}:{path_var}",
            }
        )

    @contextlib.asynccontextmanager
    async def run_command_on_host(
        self,
        command: str,
        env: Optional[Dict[str, str]] = None,
        command_timeout: float = 300,
    ) -> Iterator[Tuple[asyncio.Task, PatternMatchingWaitableMonitor]]:
        """Run `command` on host in given `env` and with optional `timeout`.

        The command is run in the environment extending `env` with variables needed
        to communicate with the daemon running in this probe's container.

        Internally, this method used `process.run_command()` to run `command`.
        The argument `command_timeout` is passed as the `timeout` parameter to
        `process.run_command()`.

        Returns the `asyncio` task that logs output from the command, and an event
        monitor that observes lines out output produced by the command.

        The task can be awaited in order to wait until the command completes.
        The monitor can be used for asserting properties of the command's output.
        """
        cmd_env = {**env} if env is not None else {}
        self.set_agent_env_vars(cmd_env)

        cmd_monitor = PatternMatchingWaitableMonitor(name="command output")
        cmd_monitor.start()

        try:
            with monitored_logger(
                f"goth.{self.name}.command_output", cmd_monitor
            ) as cmd_logger:
                cmd_task = asyncio.create_task(
                    process.run_command(
                        command.split(),
                        cmd_env,
                        log_level=logging.INFO,
                        cmd_logger=cmd_logger,
                        timeout=command_timeout,
                    )
                )
                yield cmd_task, cmd_monitor

        except Exception as e:
            logger.warning(f"Cancelling command on error: {e!r}")
            if cmd_task and not cmd_task.done():
                cmd_task.cancel()
            raise

        finally:
            await cmd_monitor.stop()
            logger.debug("Waiting for the command to finish")
            await asyncio.gather(cmd_task, return_exceptions=True)


@contextlib.contextmanager
def create_probe(
    runner: "Runner",
    docker_client: DockerClient,
    config: YagnaContainerConfig,
    log_config: LogConfig,
) -> Iterator[Probe]:
    """Implement a ContextManager protocol for creating and removing probes."""

    probe: Optional[Probe] = None
    try:
        probe = config.probe_type(runner, docker_client, config, log_config)
        for name, value in config.probe_properties.items():
            probe.__setattr__(name, value)
        yield probe
    finally:
        if probe:
            probe.remove()


@contextlib.asynccontextmanager
async def run_probe(probe: Probe) -> AsyncIterator[str]:
    """Implement AsyncContextManager for starting and stopping a probe."""

    try:
        await probe.start()
        assert probe.ip_address
        yield probe.ip_address
    finally:
        await probe.stop()


class RequestorProbe(ApiClientMixin, Probe):
    """A requestor probe that can make calls to Yagna REST APIs.

    This class is used in Level 1 scenarios and as a type of `self`
    argument for `Market/Payment/ActivityOperationsMixin` methods.
    """

    _api_base_host: str
    """Base hostname for the Yagna API clients."""

    def __init__(
        self,
        runner: "Runner",
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
    ):
        super().__init__(runner, client, config, log_config)
        host_port = self.container.ports[YAGNA_REST_PORT]
        proxy_ip = "127.0.0.1"  # use the host-mapped proxy port
        self._api_base_host = YAGNA_REST_URL.substitute(host=proxy_ip, port=host_port)

    async def _start_container(self) -> None:
        await super()._start_container()

        self.cli.payment_fund()
        self.cli.payment_init(sender_mode=True)


class ProviderProbe(AgentMixin, Probe):
    """A probe subclass that can run a provider agent."""

    agent_preset: Optional[str]
    """Name of the preset to be used when placing a market offer."""

    subnet: str
    """Name of the subnet to which the provider agent connects."""

    def __init__(
        self,
        runner: "Runner",
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        agent_preset: Optional[str] = None,
        subnet: str = DEFAULT_SUBNET,
    ):
        super().__init__(runner, client, config, log_config)
        self.agent_preset = agent_preset
        self.subnet = subnet

    async def start_agent(self):
        """Start the provider agent and attach to its log stream."""

        self._logger.info("Starting ya-provider")

        if self.agent_preset:
            self.container.exec_run(f"ya-provider preset activate {self.agent_preset}")
        self.container.exec_run(f"ya-provider config set --subnet {self.subnet}")

        log_stream = self.container.exec_run(
            f"ya-provider run" f" --app-key {self.app_key} --node-name {self.name}",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)
