"""Classes and helpers for managing Probes."""

import abc
import logging
from pathlib import Path
import time
from typing import Optional, TypeVar, TYPE_CHECKING

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
from goth.runner.container.yagna import YagnaContainer, YagnaContainerConfig
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

    key_file: Optional[str]
    """Keyfile to be imported into the yagna daemon id service."""

    _docker_client: DockerClient
    """A docker client used to create the deamon's container."""

    def __init__(
        self,
        runner: "Runner",
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
    ):
        self.runner = runner
        self._docker_client = client
        self.container = YagnaContainer(client, config, log_config, assets_path)
        self.cli = Cli(self.container).yagna
        self._logger = ProbeLoggingAdapter(
            logger, {ProbeLoggingAdapter.EXTRA_PROBE_NAME: self.name}
        )
        self.ip_address = None
        self.key_file = config.key_file

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

    def start(self) -> None:
        """Start the probe.

        This method is extended in subclasses and mixins.
        """

        self._start_container()

    async def stop(self):
        """
        Stop the probe, removing the Docker container of the daemon being tested.

        Once stopped, a probe cannot be restarted.
        """
        if self.container.logs:
            await self.container.logs.stop()
        self.container.remove(force=True)

    def _start_container(self) -> None:
        """
        Start the probe's Docker container.

        Performs all necessary steps to make the daemon ready for testing
        (e.g. creating the default app key).
        """
        self.container.start()
        # Give the daemon some time to start before asking it for an app key.
        time.sleep(1)
        self.create_app_key()

        # Obtain the IP address of the container
        self.ip_address = get_container_address(
            self._docker_client, self.container.name
        )
        self._logger.info("IP address: %s", self.ip_address)

    def create_app_key(self, key_name: str = "test_key") -> str:
        """Attempt to create a new app key on the Yagna daemon.

        The key name can be specified via `key_name` parameter.
        Return the key as string.

        When `self.key_file` is set, this method also:
        - creates ID based on `self.key_file`
        - sets this new ID as default
        - restarts the container ( https://github.com/golemfactory/yagna/issues/458 )
        """
        address = None
        if self.key_file:
            self._logger.debug(
                "create_id(alias=%s, key_file=%s", key_name, self.key_file
            )
            try:
                db_id = self.cli.id_create(alias=key_name, key_file=self.key_file)
                address = db_id.address
                self._logger.debug("create_id. alias=%s, address=%s", db_id, address)
            except KeyAlreadyExistsError as e:
                logger.critical("Id already exists : (%r)", e)
                raise
                # db_id = next(
                #     filter(lambda i: i.id == e.TODO_extract_id(), self.cli.id_list())
                # )
                # address = db_id.address
            db_id = self.cli.id_update(address, set_default=True)
            self._logger.debug("update_id. result=%r", db_id)
            self.container.restart()
            time.sleep(1)
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

    _use_agent: bool = False
    """Indicates whether ya-requestor binary should be started in this node.

    The use of ya-requestor is deprecated and supported for the sake of level 0 test
    scenario compatibility.
    """

    def __init__(
        self,
        runner: "Runner",
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
    ):
        super().__init__(runner, client, config, log_config, assets_path)

        host_port = self.container.ports[YAGNA_REST_PORT]
        proxy_ip = get_container_address(client, PROXY_HOST)
        self._api_base_host = YAGNA_REST_URL.substitute(host=proxy_ip, port=host_port)


class RequestorProbeWithAgent(AgentMixin, RequestorProbe):
    """A probe subclass that can run a requestor agent.

    The use of ya-requestor is deprecated and supported for the sake of level 0 test
    scenario compatibility.
    """

    def start_agent(self):
        """Start the requestor agent and attach to its log stream."""

        # TODO: Serve the package from a local server
        # https://github.com/golemfactory/yagna-integration/issues/249
        log_stream = self.container.exec_run(
            "ya-requestor"
            f" --app-key {self.app_key} --exe-script /asset/exe_script.json"
            " --task-package "
            "hash://sha3:d5e31b2eed628572a5898bf8c34447644bfc4b5130cfc1e4f10aeaa1:"
            "http://3.249.139.167:8000/rust-wasi-tutorial.zip",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)


class ProviderProbe(AgentMixin, Probe):
    """A probe subclass that can run a provider agent."""

    agent_preset: str = "default"
    """Name of the preset to be used when placing a market offer."""

    def start_agent(self) -> None:
        """Start the provider agent and attach to its log stream."""

        self.container.exec_run(
            f"ya-provider preset activate {self.agent_preset}",
        )
        log_stream = self.container.exec_run(
            f"ya-provider run" f" --app-key {self.app_key} --node-name {self.name}",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)


ProbeType = TypeVar("ProbeType")
