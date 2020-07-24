"""Classes and helpers for managing Probes."""

import abc
import logging
from pathlib import Path
import time
from typing import Optional, Type

from docker import DockerClient

import openapi_activity_client as activity
import openapi_market_client as market
import openapi_payment_client as payment
from goth.address import (
    ensure_no_trailing_slash,
    ACTIVITY_API_URL,
    MARKET_API_URL,
    PAYMENT_API_URL,
    PROXY_HOST,
    YAGNA_REST_PORT,
    YAGNA_REST_URL,
)
from goth.runner.cli import Cli, YagnaDockerCli
from goth.runner.container.utils import get_container_address
from goth.runner.container.yagna import YagnaContainer, YagnaContainerConfig
from goth.runner.exceptions import KeyAlreadyExistsError
from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEventMonitor

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

    cli: YagnaDockerCli
    """A module which enables calling the Yagna CLI on the daemon being tested."""
    container: YagnaContainer
    """A module which handles the lifecycle of the daemon's Docker container."""
    ip_address: Optional[str]
    """An IP address of the daemon's container in the Docker network."""
    _docker_client: DockerClient
    """A docker client used to create the deamon's container."""

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
    ):
        self._docker_client = client
        self.container = YagnaContainer(client, config, log_config, assets_path)
        self.cli = Cli(self.container).yagna
        agent_log_config = LogConfig(
            file_name=f"{self.name}_agent", base_dir=self.container.log_config.base_dir,
        )
        # FIXME: Move agent logs to ProviderProbe when level0 is removed
        self.agent_logs = LogEventMonitor(agent_log_config)

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

    def start_container(self) -> None:
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
        """
        address = None
        if self.key_file:
            self._logger.debug(
                "create_id(alias=%s, key_file=%s", key_name, self.key_file
            )
            try:
                db_id = self.cli.id_create(alias=key_name, key_file=self.key_file)
                address = db_id.address
                self._logger.debug("create_id. alias=%s, address=%s", id, address)
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
            key = self.cli.app_key_create(name=key_name, alias_or_addr=address)
            self._logger.debug("create_app_key. key_name=%s, key=%s", key_name, key)
        except KeyAlreadyExistsError:
            app_key = next(
                filter(lambda k: k.name == key_name, self.cli.app_key_list())
            )
            key = app_key.key
        return key

    @abc.abstractmethod
    def start_agent(self):
        """Start the agent."""

    async def stop(self):
        """
        Stop the probe, removing the Docker container of the daemon being tested.

        Once stopped, a probe cannot be restarted.
        """
        if self.container.logs:
            await self.container.logs.stop()
        if self.agent_logs:
            await self.agent_logs.stop()
        self.container.remove(force=True)


class ActivityApiClient:
    """
    Client for the activity API of a Yagna daemon.

    The activity API is divided into two domains: control and state. This division is
    reflected in the inner client objects of this class.
    """

    control: activity.RequestorControlApi
    """Client for the control part of the activity API."""

    state: activity.RequestorStateApi
    """Client for the state part of the activity API."""

    def __init__(self, app_key: str, address: str, logger: logging.Logger):
        api_url = ACTIVITY_API_URL.substitute(base=address)
        api_url = ensure_no_trailing_slash(str(api_url))
        config = activity.Configuration(host=api_url)
        config.access_token = app_key
        client = activity.ApiClient(config)

        self.control = activity.RequestorControlApi(client)
        self.state = activity.RequestorStateApi(client)
        logger.debug("activity API initialized. url=%s", api_url)


class RequestorProbe(Probe):
    """
    Provides a testing interface for a Yagna node acting as a requestor.

    This includes activity, market and payment API clients which can be used to
    directly control the requestor daemon.
    """

    activity: ActivityApiClient
    """Activity API client for the requestor daemon."""
    market: market.ApiClient
    """Market API client for the requestor daemon."""
    payment: payment.ApiClient
    """Payment API client for the requestor daemon."""

    _api_base_host: str
    """Base hostname for the Yagna API clients."""

    _use_agent: bool = False
    """Indicates whether ya-requestor binary should be started in this node.

    The use of ya-requestor is deprecated and supported for the sake of level 0 test
    scenario compatibility.
    """

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
    ):
        super().__init__(client, config, log_config, assets_path)

        host_port = self.container.ports[YAGNA_REST_PORT]
        proxy_ip = get_container_address(client, PROXY_HOST)
        self._api_base_host = YAGNA_REST_URL.substitute(host=proxy_ip, port=host_port)
        self._use_agent = config.use_requestor_agent

    def start_agent(self):
        """Start the yagna container and initialize the requestor agent."""

        if self._use_agent:
            self._start_requestor_agent()
        else:
            self.activity = ActivityApiClient(
                self.app_key, self._api_base_host, self._logger
            )
            self._init_payment_api()
            self._init_market_api()

    def _start_requestor_agent(self):
        """Start provider agent on the container and initialize its LogMonitor."""
        self.cli.payment_init(address=self.address, requestor_mode=True)
        log_stream = self.container.exec_run(
            "ya-requestor"
            f" --app-key {self.app_key} --exe-script /asset/exe_script.json"
            " --task-package "
            "hash://sha3:d5e31b2eed628572a5898bf8c34447644bfc4b5130cfc1e4f10aeaa1:"
            "http://3.249.139.167:8000/rust-wasi-tutorial.zip",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)

    def _init_market_api(self):
        api_url = MARKET_API_URL.substitute(base=self._api_base_host)
        api_url = ensure_no_trailing_slash(str(api_url))
        config = market.Configuration(host=api_url)
        config.access_token = self.app_key
        client = market.ApiClient(config)
        self.market = market.RequestorApi(client)
        self._logger.debug("market API initialized. url=%s", api_url)

    def _init_payment_api(self):
        api_url = PAYMENT_API_URL.substitute(base=self._api_base_host)
        api_url = ensure_no_trailing_slash(str(api_url))
        config = payment.Configuration(host=api_url)
        config.access_token = self.app_key
        client = payment.ApiClient(config)
        self.payment = payment.RequestorApi(client)
        self._logger.debug("payment API initialized. url=%s", api_url)


class ProviderProbe(Probe):
    """Provides a testing interface for a Yagna node acting as a provider."""

    agent_logs: Optional[LogEventMonitor]
    """
    Monitor and buffer for provider agent logs, enables asserting for certain lines to
    be present in the log buffer.
    """
    agent_preset: str
    """Name of the preset to be used when placing a market offer."""

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
        preset_name: str = "default",
    ):
        super().__init__(client, config, log_config, assets_path=assets_path)
        self.agent_preset = preset_name

    def start_agent(self):
        """Start the agent and attach the log monitor."""

        self.container.exec_run(f"ya-provider preset activate {self.agent_preset}",)
        self.cli.payment_init(address=self.address, provider_mode=True)
        log_stream = self.container.exec_run(
            f"ya-provider run" f" --app-key {self.app_key} --node-name {self.name}",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)

    async def stop(self):
        """Stop the agent and the log monitor."""
        if self.agent_logs is not None:
            await self.agent_logs.stop()
        await super().stop()


Provider = ProviderProbe
Requestor = RequestorProbe
Role = Type[Probe]
