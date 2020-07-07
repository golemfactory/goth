import abc
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path
from string import Template
from typing import Optional

from docker import DockerClient

import openapi_activity_client as activity
import openapi_market_client as market
import openapi_payment_client as payment
from goth.address import (
    ACTIVITY_API_URL,
    MARKET_API_URL,
    PAYMENT_API_URL,
    YAGNA_REST_URL,
)
from goth.runner.cli import Cli, YagnaDockerCli
from goth.runner.container.yagna import YagnaContainer, YagnaContainerConfig
from goth.runner.exceptions import KeyAlreadyExistsError
from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEventMonitor

logger = logging.getLogger(__name__)


class Role(Enum):
    requestor = 0
    provider = 1


class Probe(abc.ABC):
    """
    Provides a unified interface for interacting with and testing a single Yagna node
    running as part of an integration test. This interface consists of several
    independent modules which may be extended in subclasses
    (see `ProviderProbe` and `RequestorProbe`).
    """

    cli: YagnaDockerCli
    """A module which enables calling the Yagna CLI on the daemon being tested"""
    container: YagnaContainer
    """A module which handles the lifecycle of the daemon's Docker container"""

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
    ):
        self.container = YagnaContainer(client, config, log_config, assets_path)
        self.cli = Cli(self.container).yagna

    def __str__(self):
        return self.name

    @property
    def address(self) -> Optional[str]:
        """Return the address for the Yagna daemon identity marked as default"""
        identity = self.cli.id_show()
        return identity.address if identity else None

    @property
    def app_key(self) -> Optional[str]:
        """Return the first app key from this probe's Yagna daemon"""
        keys = self.cli.app_key_list()
        return keys[0].key if keys else None

    @property
    def name(self) -> str:
        return self.container.name

    def create_app_key(self, key_name: str = "test_key") -> str:
        """
        Attempt to create a new app key on the Yagna daemon. The key name can be
        specified via `key_name` parameter.
        Return the key as string.
        """
        try:
            key = self.cli.app_key_create(key_name)
            logger.debug("create_app_key. key_name=%s, key=%s", key_name, key)
        except KeyAlreadyExistsError:
            app_key = next(
                filter(lambda k: k.name == key_name, self.cli.app_key_list())
            )
            key = app_key.key
        return key

    def start(self):
        """
        Start the probe, performing all necessary steps to make the daemon ready for
        testing (e.g. starting the Docker container, creating the default app key).
        """
        self.container.start()
        self.create_app_key()

    async def stop(self):
        """
        Stop the probe, removing the Docker container of the daemon being tested.
        Once stopped, a probe cannot be restarted.
        """
        if self.container.logs is not None:
            await self.container.logs.stop()
        self.container.remove(force=True)


class ActivityApiClient:
    """
    Client for the activity API of a Yagna daemon. The activity API is divided into two
    domains: control and state. This division is reflected in the inner client objects
    of this class.
    """

    control: activity.RequestorControlApi
    """Client for the control part of the activity API"""

    state: activity.RequestorStateApi
    """Client for the state part of the activity API"""

    def __init__(self, app_key: str, address: str, node_name: str):
        api_url = ACTIVITY_API_URL.substitute(base=address)
        config = activity.Configuration(host=api_url)
        config.access_token = app_key
        client = activity.ApiClient(config)

        self.control = activity.RequestorControlApi(client)
        self.state = activity.RequestorStateApi(client)
        logger.debug(
            "activity API initialized. node_name=%s, url=%s", node_name, api_url
        )


class RequestorProbe(Probe):
    """
    Provides a testing interface for a Yagna node acting as a requestor.
    This includes activity, market and payment API clients which can be used to
    directly control the requestor daemon.
    """

    activity: ActivityApiClient
    """Activity API client for the requestor daemon"""
    market: market.ApiClient
    """Market API client for the requestor daemon"""
    payment: payment.ApiClient
    """Payment API client for the requestor daemon"""

    def start(self):
        super().start()

        host_port = self.container.ports[YagnaContainer.HTTP_PORT]
        daemon_base_url = YAGNA_REST_URL.substitute(host="localhost", port=host_port)

        self.activity = ActivityApiClient(self.app_key, daemon_base_url, self.name)
        self._init_payment_api(daemon_base_url)
        self._init_market_api(daemon_base_url)

        # TODO Remove once agent calls are implemented via probe
        self.start_requestor_agent()

    # TODO Remove once agent calls are implemented via probe
    def start_requestor_agent(self):
        log_stream = self.container.exec_run(
            f"ya-requestor"
            f" --app-key {self.app_key} --exe-script /asset/exe_script.json",
            stream=True,
        )
        self._init_agent_logs(log_stream)

    # TODO Remove once agent calls are implemented via probe
    def _init_agent_logs(self, log_stream):
        log_config = LogConfig(
            file_name=f"{self.name}_agent", base_dir=self.container.log_config.base_dir,
        )
        self.agent_logs = LogEventMonitor(log_stream.output, log_config)

    def _init_market_api(self, address: str):
        api_url = MARKET_API_URL.substitute(base=address)
        config = market.Configuration(host=api_url)
        config.access_token = self.app_key
        client = market.ApiClient(config)
        self.market = market.RequestorApi(client)
        logger.debug("market API initialized. node_name=%s, url=%s", self.name, api_url)

    def _init_payment_api(self, address: str):
        api_url = PAYMENT_API_URL.substitute(base=address)
        config = payment.Configuration(host=api_url)
        config.access_token = self.app_key
        client = payment.ApiClient(config)
        self.payment = payment.RequestorApi(config)
        logger.debug(
            "payment API initialized. node_name=%s, url=%s", self.name, api_url
        )


class ProviderProbe(Probe):
    """Provides a testing interface for a Yagna node acting as a provider."""

    agent_logs: LogEventMonitor
    """
    Monitor and buffer for provider agent logs, enables asserting for certain lines to
    be present in the log buffer
    """
    agent_preset: str
    """Name of the preset to be used when placing a market offer"""

    def __init__(
        self,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
        preset_name: str = "amazing-offer",
    ):
        super().__init__(client, config, log_config, assets_path=assets_path)
        self.agent_preset = preset_name

    def start(self):
        super().start()
        log_stream = self.container.exec_run(
            f"ya-provider run"
            f" --app-key {self.app_key} --node-name {self.name} {self.agent_preset}",
            stream=True,
        )
        self._init_agent_logs(log_stream)

    async def stop(self):
        if self.agent_logs is not None:
            await self.agent_logs.stop()
        await super().stop()

    def _init_agent_logs(self, log_stream):
        log_config = LogConfig(
            file_name=f"{self.name}_agent", base_dir=self.container.log_config.base_dir,
        )
        self.agent_logs = LogEventMonitor(log_stream.output, log_config)
