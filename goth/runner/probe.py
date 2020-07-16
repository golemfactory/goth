"""Classes and helpers for managing Probes."""

import abc
from enum import Enum
import logging
from pathlib import Path
import time
from typing import Optional

from docker import DockerClient

import openapi_activity_client as activity
import openapi_market_client as market
import openapi_payment_client as payment
from goth.address import (
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


class Role(Enum):
    """Role of the probe."""

    requestor = 0
    provider = 1


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

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
    ):
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

    def create_app_key(self, key_name: str = "test_key") -> str:
        """Attempt to create a new app key on the Yagna daemon.

        The key name can be specified via `key_name` parameter.
        Return the key as string.
        """
        try:
            key = self.cli.app_key_create(key_name)
            self._logger.debug("create_app_key. key_name=%s, key=%s", key_name, key)
        except KeyAlreadyExistsError:
            app_key = next(
                filter(lambda k: k.name == key_name, self.cli.app_key_list())
            )
            key = app_key.key
        return key

    def start(self):
        """
        Start the probe.

        Performs all necessary steps to make the daemon ready for testing
        (e.g. starting the Docker container, creating the default app key).
        """
        self.container.start()
        # Give the daemon some time to start before asking it for an app key.
        time.sleep(1)
        self.create_app_key()

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

    def start(self):
        """Start the yagna container and initialize the requestor agent."""
        super().start()

        self.activity = ActivityApiClient(
            self.app_key, self._api_base_host, self._logger
        )
        self._init_payment_api()
        self._init_market_api()

        # TODO Remove once agent calls are implemented via probe
        self.start_requestor_agent()

    # TODO Remove once agent calls are implemented via probe
    def start_requestor_agent(self):
        """Start provider agent on the container and initialize its LogMonitor."""
        log_stream = self.container.exec_run(
            "ya-requestor"
            f" --app-key {self.app_key} --exe-script /asset/exe_script.json"
            " --task-package "
            "hash://sha3:d5e31b2eed628572a5898bf8c34447644bfc4b5130cfc1e4f10aeaa1:"
            "http://34.244.4.185:8000/rust-wasi-tutorial.zip",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)

    def _init_market_api(self):
        api_url = MARKET_API_URL.substitute(base=self._api_base_host)
        config = market.Configuration(host=api_url)
        config.access_token = self.app_key
        client = market.ApiClient(config)
        self.market = market.RequestorApi(client)
        self._logger.debug("market API initialized. url=%s", api_url)

    def _init_payment_api(self):
        api_url = PAYMENT_API_URL.substitute(base=self._api_base_host)
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

    def start(self):
        """Start the agents and attach the log monitor."""
        super().start()
        self.container.exec_run(f"ya-provider preset activate {self.agent_preset}",)
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
