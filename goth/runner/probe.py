"""Classes and helpers for managing Probes."""

import abc
import asyncio
import logging
from typing import Optional, TYPE_CHECKING

from docker import DockerClient

from goth.address import (
    YAGNA_REST_PORT,
    PROXY_HOST,
    YAGNA_REST_URL,
)
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
from goth.runner.log import LogConfig

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

    ip_address: Optional[str]
    """An IP address of the daemon's container in the Docker network."""

    _docker_client: DockerClient
    """A docker client used to create the deamon's container."""

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
        self.container = YagnaContainer(client, config, log_config)
        self.cli = Cli(self.container).yagna
        self._logger = ProbeLoggingAdapter(
            logger, {ProbeLoggingAdapter.EXTRA_PROBE_NAME: self.name}
        )
        self.ip_address = None
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
        self.container.remove(force=True)

    async def _start_container(self) -> None:
        """
        Start the probe's Docker container.

        Performs all necessary steps to make the daemon ready for testing
        (e.g. creating the default app key).
        """
        self.container.start()

        # Wait until the daemon is ready to create an app key.
        self._logger.info("Waiting for GSB identity service to be available")
        if self.container.logs:
            await self.container.logs.wait_for_entry(
                ".*Identity GSB service successfully activated", timeout=30
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
        proxy_ip = '127.0.0.1' # use the host-mapped proxy port
        self._api_base_host = YAGNA_REST_URL.substitute(host=proxy_ip, port=host_port)


class RequestorProbeWithAgent(AgentMixin, RequestorProbe):
    """A probe subclass that can run a requestor agent.

    The use of ya-requestor is deprecated and supported for the sake of level 0 test
    scenario compatibility.
    """

    task_package: str
    """Value of the `--task-package` argument to `ya-requestor` run by this probe.

    This string may include `{web_server_addr}` and `{web_server_port}` placeholders
    which will be replaced by the IP address and the port, respectively,
    of the built-in web server.
    """

    def __init__(
        self,
        runner: "Runner",
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
    ):
        super().__init__(runner, client, config, log_config)

    async def start_agent(self):
        """Start the requestor agent and attach to its log stream."""

        self._logger.info("Starting ya-requestor")

        pkg_spec = self.task_package.format(
            web_server_addr=self.runner.host_address,
            web_server_port=self.runner.web_server_port,
        )
        log_stream = self.container.exec_run(
            "ya-requestor"
            f" --app-key {self.app_key} --exe-script /asset/exe_script.json"
            f" --task-package {pkg_spec}",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)


class ProviderProbe(AgentMixin, Probe):
    """A probe subclass that can run a provider agent."""

    agent_preset: Optional[str]
    """Name of the preset to be used when placing a market offer."""

    def __init__(
        self,
        runner: "Runner",
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        agent_preset: Optional[str] = None,
    ):
        super().__init__(runner, client, config, log_config)
        self.agent_preset = agent_preset

    async def start_agent(self):
        """Start the provider agent and attach to its log stream."""

        self._logger.info("Starting ya-provider")

        if self.agent_preset:
            self.container.exec_run(f"ya-provider preset activate {self.agent_preset}")

        log_stream = self.container.exec_run(
            f"ya-provider run" f" --app-key {self.app_key} --node-name {self.name}",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)
