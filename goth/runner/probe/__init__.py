"""Package related to goth's probe interface."""

import abc
import asyncio
from collections import OrderedDict
import contextlib
import copy
import logging
import os
from pathlib import Path
import shlex
import signal
import traceback
from time import perf_counter
from typing import (
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    TYPE_CHECKING,
)

import aiohttp
from docker import DockerClient

from goth.address import (
    HOST_NGINX_PORT_OFFSET,
    YAGNA_BUS_URL,
    YAGNA_REST_PORT,
    YAGNA_REST_URL,
)

from goth import gftp
from goth.node import DEFAULT_SUBNET
from goth.payment_config import PaymentConfig
from goth.runner import process
from goth.runner.cli import Cli, YagnaDockerCli
from goth.runner.container.utils import get_container_address
from goth.runner.container.yagna import (
    YagnaContainer,
    YagnaContainerConfig,
)
from goth.runner.exceptions import KeyAlreadyExistsError, TemporalAssertionError
from goth.runner.log import LogConfig, monitored_logger
from goth.runner.log_monitor import PatternMatchingEventMonitor
from goth.runner.probe.agent import AgentComponent, ProviderAgentComponent
from goth.runner.probe.mixin import ActivityApiMixin, MarketApiMixin, PaymentApiMixin
from goth.runner.probe.rest_client import RestApiComponent

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

    api: RestApiComponent
    """Component with clients for all three yagna REST APIs."""

    runner: "Runner"
    """A runner that created this probe."""

    cli: YagnaDockerCli
    """A module which enables calling the Yagna CLI on the daemon being tested."""

    container: YagnaContainer
    """A module which handles the lifecycle of the daemon's Docker container."""

    ip_address: Optional[str] = None
    """An IP address of the daemon's container in the Docker network."""

    _agents: "OrderedDict[str, AgentComponent]"
    """Collection of agent components that will be started as part of this probe.

    Keys are agent names, values are subclasses of `AgentComponent`.
    """

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
        self._agents = OrderedDict()
        self._docker_client = client
        self._logger = ProbeLoggingAdapter(
            logger, {ProbeLoggingAdapter.EXTRA_PROBE_NAME: config.name}
        )
        config = self._setup_gftp_proxy(config)
        private_key = None

        # This part is a hack to allow using specific private keys for specific addresses
        # Issue: https://github.com/golemfactory/goth/issues/655
        if config.payment_id:
            if config.payment_id.key.address == "63fc2ad3d021a4d7e64323529a55a9442c444da0":
                self._logger.info("Setting private key 1...")
                private_key = "5c8b9227cd5065c7e3f6b73826b8b42e198c4497f6688e3085d5ab3a6d520e74"
            elif config.payment_id.key.address == "17ec8597ff92c3f44523bdc65bf0f1be632917ff":
                self._logger.info("Setting private key 2...")
                private_key = "29f3edee0ad3abf8e2699402e0e28cd6492c9be7eaab00d732a791c33552f797"
            elif config.payment_id.key.address == "d1d84f0e28d6fedf03c73151f98df95139700aa7":
                self._logger.info("Setting private key 3...")
                private_key = "50c8b3fc81e908501c8cd0a60911633acaca1a567d1be8e769c5ae7007b34b23"
            else:
                # Suppress error message if the payment_id is a mock object
                if str(type(config.payment_id)) != "<class 'unittest.mock.MagicMock'>":
                    self._logger.error(
                        "Private key not found for address: {}".format(str(type(config)))
                    )

        if private_key:
            config.environment["YAGNA_AUTOCONF_ID_SECRET"] = private_key

        self.container = YagnaContainer(client, config, log_config)
        self.cli = Cli(self.container).yagna
        self._yagna_config = config

    def __str__(self):
        return self.name

    @property
    def agents(self) -> List[AgentComponent]:
        """List of agent components that will be started as part of this probe."""
        return list(self._agents.values())

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

    @property
    def payment_config(self) -> PaymentConfig:
        """Payment configuration used for setting up this probe's yagna node."""
        return self._yagna_config.payment_config

    @property
    def uses_proxy(self) -> bool:
        """Return `True` iff this probe is configured to use MITM proxy."""
        return self._yagna_config.use_proxy

    @property
    def host_rest_port(self) -> int:
        """Host port to which yagna API port on this probe's container is mapped to."""
        return self.container.ports[YAGNA_REST_PORT]

    @property
    def nginx_rest_port(self) -> int:
        """Host port to which the nginx port assigned to this probe is mapped to."""
        return self.host_rest_port + HOST_NGINX_PORT_OFFSET

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

    def add_agent(self, agent: AgentComponent) -> None:
        """Add an agent to be started for this probe."""
        if self._agents.get(agent.name):
            raise KeyAlreadyExistsError(
                f"Probe already has agent component with name: `{agent.name}`"
            )
        self._agents[agent.name] = agent

    async def start(self) -> None:
        """Start the probe."""

        await self._start_container()
        self.api = RestApiComponent(self)

    async def start_agents(self):
        """Start all of the probe's agents."""
        for agent in self.agents:
            await agent.start()

    async def stop(self):
        """
        Stop the probe, removing the Docker container of the daemon being tested.

        Once stopped, a probe cannot be restarted.
        """
        self._logger.info("Stopping probe")
        for agent in self.agents:
            await agent.stop()
        if self.container.logs:
            await self.container.logs.stop()
        self.container.stop()

    def remove(self) -> None:
        """Remove the underlying container."""
        if self.container:
            self.container.remove(force=True)
            self._logger.debug("Container removed")

    async def _wait_for_yagna_start(self, timeout: float = 30) -> None:
        host_yagna_addr = f"http://127.0.0.1:{self.container.ports[YAGNA_REST_PORT]}"
        self._logger.info(f"Waiting for yagna REST API: {host_yagna_addr}")
        self._logger.info(
            f"Waiting for yagna http endpoint: {host_yagna_addr}, timeout: {timeout:.1f}"
        )
        start_time = perf_counter()
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(f"{host_yagna_addr}/version/get") as resp:
                        yagna_status_obj = await resp.json()
                        yagna_version = yagna_status_obj["current"]["version"]
                        elapsed = perf_counter() - start_time
                        self._logger.info(
                            f"Yagna responded with version: {yagna_version}"
                            f" after {elapsed:.1f}/{timeout:.1f} seconds"
                        )
                        if timeout - elapsed < 5:
                            self._logger.warning(
                                f"Only {timeout - elapsed:.1f} seconds left to timeout. "
                                "Consider using a higher timeout."
                            )
                        return yagna_version
                except aiohttp.ClientConnectionError as ex:
                    self._logger.debug(f"Failed to connect to yagna - trying again: {ex}")
                    pass

                elapsed = perf_counter() - start_time
                if elapsed > timeout:
                    raise Exception(
                        f"Timeout {timeout} exceeded: "
                        f"Failed to get data from endpoint: {host_yagna_addr}"
                    )

                await asyncio.sleep(0.5)

    async def _start_container(self) -> None:
        """
        Start the probe's Docker container.

        Performs all necessary steps to make the daemon ready for testing
        (e.g. creating the default app key).
        """

        self.container.start()

        await self._wait_for_yagna_start(60)

        await self.create_app_key()

        # Obtain the IP address of the container
        self.ip_address = get_container_address(self._docker_client, self.container.name)
        nginx_ip_address = self.runner.nginx_container_address

        self._logger.info(
            "Yagna API host:port in Docker network: " "%s:%s (direct), %s:%s (through proxy)",
            self.ip_address,
            YAGNA_REST_PORT,
            nginx_ip_address,
            self.host_rest_port,
        )
        self._logger.info(
            "Yagna API host:port via localhost: "
            "127.0.0.1:%s (direct), 127.0.0.1:%s (through proxy)",
            self.host_rest_port,
            self.nginx_rest_port,
        )

    async def create_app_key(self, key_name: str = "test_key") -> str:
        """Attempt to create a new app key on the Yagna daemon.

        The key name can be specified via `key_name` parameter.
        Return the key as string.
        """
        try:
            key = self.cli.app_key_create(key_name)
            self._logger.debug("create_app_key. key_name=%s, key=%s", key_name, key)
        except KeyAlreadyExistsError:
            app_key = next(filter(lambda k: k.name == key_name, self.cli.app_key_list()))
            key = app_key.key
        return key

    def get_yagna_api_url(self) -> str:
        """Return the URL through which this probe's daemon can be reached.

        This URL can be used to access yagna APIs from outside of the probe's
        container, for example, from a requestor script running on host.

        The URL may point directly to the IP address of this probe in the Docker
        network, or a port on localhost on which the MITM proxy listens, depending
        on the `use_proxy` setting in the probe's configuration.
        """

        # Port on the host to which yagna API port in the container is mapped
        host_port = self.nginx_rest_port if self.uses_proxy else self.host_rest_port
        return YAGNA_REST_URL.substitute(host="127.0.0.1", port=host_port)

    def get_agent_env_vars(self, expand_path: bool = True) -> Dict[str, str]:
        """Get env vars needed to talk to the daemon in this probe's container.

        The returned vars include the `PATH` variable as it needs to contain the
        directory in which the gftp proxy script resides.
        The value of the result's `PATH` variable gets prefixed with the gftp script's
        directory, so it will look like this: `/tmp/some_gftp_dir:$PATH`.

        When `expand_path` is `True` (default behaviour) the `$PATH` in the above
        example gets expanded to the system's actual `PATH` variable (taken from
        `os.environ`).
        When `expand_path` is `False` the `$PATH` part stays as-is (useful for shell
        substitution).
        """

        if not self.app_key:
            raise AttributeError("Yagna application key is not set yet")

        path: str = os.environ["PATH"] if expand_path else "$PATH"

        return {
            "YAGNA_APPKEY": self.app_key,
            "YAGNA_API_URL": self.get_yagna_api_url(),
            "GSB_URL": YAGNA_BUS_URL.substitute(host=self.ip_address),
            "PATH": f"{self._gftp_script_dir}:{path}",
        }

    @contextlib.asynccontextmanager
    async def run_command_on_host(
        self,
        command: str,
        env: Optional[Mapping[str, str]] = None,
        command_timeout: float = 300,
    ) -> AsyncIterator[Tuple[asyncio.Task, PatternMatchingEventMonitor, process.ProcessMonitor]]:
        """Run `command` on host in given `env` and with optional `timeout`.

        The command is run in the environment extending `env` with variables needed
        to communicate with the daemon running in this probe's container.

        Internally, this method uses `process.run_command()` to run `command`.
        The argument `command_timeout` is passed as the `timeout` parameter to
        `process.run_command()`.

        Returns the `asyncio` task that logs output from the command, and an event
        monitor that observes lines of output produced by the command.

        The task can be awaited in order to wait until the command completes.
        The monitor can be used for asserting properties of the command's output.
        """
        cmd_env = {**env} if env is not None else {}
        cmd_env.update(self.get_agent_env_vars())

        cmd_monitor: PatternMatchingEventMonitor = PatternMatchingEventMonitor(
            name="command output"
        )
        cmd_monitor.start()

        process_monitor = process.ProcessMonitor()

        try:
            with monitored_logger(f"goth.{self.name}.command_output", cmd_monitor) as cmd_logger:
                cmd_task = asyncio.create_task(
                    process.run_command(
                        shlex.split(command),
                        cmd_env,
                        log_level=logging.INFO,
                        cmd_logger=cmd_logger,
                        timeout=command_timeout,
                        process_monitor=process_monitor,
                    )
                )
                yield cmd_task, cmd_monitor, process_monitor

                await cmd_task
                logger.debug("Command task has finished")

        except Exception as e:
            logger.error(f"Cancelling command on error: {e!r}, command: `{command}`")
            if cmd_task and not cmd_task.done():
                cmd_task.cancel()
            traceback.print_exc()
            raise

        finally:
            await cmd_monitor.stop()

            # ensure the process is killed before we leave
            proc = await process_monitor.get_process()
            try:
                proc.send_signal(signal.SIGKILL)
                await proc.wait()
            except ProcessLookupError:
                pass

            for assertion in cmd_monitor.failed:
                raise TemporalAssertionError(assertion.name)


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
        logger.debug("Creating probe. config=%s, probe_type=%s", config, config.probe_type)
        probe = config.probe_type(runner, docker_client, config, log_config)
        for name, value in config.probe_properties.items():
            probe.__setattr__(name, value)
        yield probe
    finally:
        if probe:
            logger.debug("Removing probe. name=%s", probe.name)
            probe.remove()


@contextlib.asynccontextmanager
async def run_probe(probe: Probe) -> AsyncIterator[str]:
    """Implement AsyncContextManager for starting and stopping a probe.

    Yields the probe's assigned IP address.
    """

    try:
        logger.debug("Starting probe. name=%s", probe.name)
        await probe.start()
        assert probe.ip_address
        yield probe.ip_address
    finally:
        await probe.stop()


class RequestorProbe(ActivityApiMixin, MarketApiMixin, PaymentApiMixin, Probe):
    """A probe subclass with activity API steps and requestor payment init."""

    async def _start_container(self) -> None:
        await super()._start_container()

        payment_driver = self.payment_config.driver
        self.cli.payment_fund(payment_driver)
        self.cli.payment_init(payment_driver, sender_mode=True)


class ProviderProbe(MarketApiMixin, PaymentApiMixin, Probe):
    """A probe subclass that can run a provider agent."""

    provider_agent: ProviderAgentComponent
    """The agent component running `ya-provider` for this probe.
    This field is added for convenience to make getting this agent instance easier."""

    async def _start_container(self) -> None:
        await super()._start_container()

        payment_driver = self.payment_config.driver
        self.cli.payment_fund(payment_driver)
        self.cli.payment_init(payment_driver, receiver_mode=True)

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
        self.provider_agent = ProviderAgentComponent(self, subnet, agent_preset)
        self.add_agent(self.provider_agent)
