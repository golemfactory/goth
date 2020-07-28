import dataclasses
import logging
from pathlib import Path
from typing import Optional, TypeVar

from docker import DockerClient
from typing_extensions import Protocol

import openapi_activity_client as activity
import openapi_market_client as market
import openapi_payment_client as payment

from goth.address import (
    ACTIVITY_API_URL,
    MARKET_API_URL,
    PAYMENT_API_URL,
    ensure_no_trailing_slash, YAGNA_REST_PORT, PROXY_HOST, YAGNA_REST_URL
)
from goth.runner import Runner, YagnaContainerConfig
from goth.runner.container.utils import get_container_address
from goth.runner.log import LogConfig
from goth.runner.probe import Probe, RequestorProbe


logger = logging.getLogger(__name__)


@dataclasses.dataclass
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


# Protocols `ConfigurationProtocol` and `ApiModule` and type variables
# `ConfTVar` and `ClientTVar` are used just for typing the method
# `ApiClientMixin._create_api_client()`. Not sure if it's worth it?

class ConfigurationProto(Protocol):

    access_token: str


ConfTVar = TypeVar("ConfTVar", bound=ConfigurationProto)
ClientTVar = TypeVar("ClientTVar", covariant=True)


class ApiModule(Protocol[ConfTVar, ClientTVar]):

    def Configuration(self, host: str) -> ConfTVar: pass

    def ApiClient(self, conf: ConfTVar) -> ClientTVar: pass


# TODO: This class is used as a base class for mixin classes
# with high-level market/activity/payment steps. Each subclass
# relies on a single API, so maybe we should split this base class
# into three classes? (see also TODO comments in requestor.py)
class ApiClientMixin:
    """Provides client objects for Yagna REST APIs."""

    activity: ActivityApiClient
    """Activity API client for the requestor daemon."""

    market: market.RequestorApi
    """Market API client for the requestor daemon."""

    payment: payment.RequestorApi
    """Payment API client for the requestor daemon."""

    def _create_api_client(
            self: Probe,
            api_module: ApiModule[ConfTVar, ClientTVar],
            api_url: str,
    ) -> ClientTVar:
        api_url = ensure_no_trailing_slash(str(api_url))
        config: ConfTVar = api_module.Configuration(api_url)
        config.access_token = self.app_key
        return api_module.ApiClient(config)

    def _init_activity_api(self, api_base_host: str) -> None:

        api_url = ACTIVITY_API_URL.substitute(base=api_base_host)
        client = self._create_api_client(activity, api_url)
        control = activity.RequestorControlApi(client)
        state = activity.RequestorStateApi(client)
        self.activity = ActivityApiClient(control, state)
        logger.debug("activity API initialized. url=%s", api_url)

    def _init_market_api(self, api_base_host: str) -> None:

        api_url = MARKET_API_URL.substitute(base=api_base_host)
        client = self._create_api_client(market, api_url)
        self.market = market.RequestorApi(client)
        logger.debug("market API initialized. url=%s", api_url)

    def _init_payment_api(self, api_base_host: str) -> None:

        api_url = PAYMENT_API_URL.substitute(base=api_base_host)
        client = self._create_api_client(payment, api_url)
        self.payment = payment.RequestorApi(client)
        logger.debug("payment API initialized. url=%s", api_url)


# TODO: If we split `ApiClientMixin` into three separated classes, one
# for each API, then we'd also have `Activity/Market/PaymentEnabledProbe`
# instead of just `ApiEnabledProbe`. The advantage of this would better
# control over what features are needed for a particular step, for example
# steps in `MarketOperationsMixin` should only need `self: MarketEnabledProbe`.
# The drawback of this would be proliferation of classes/mixin, possibly hard
# to manage and understand.
class ApiEnabledRequestorProbe(RequestorProbe, ApiClientMixin):
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
        runner: Runner,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
    ):
        super().__init__(runner, client, config, log_config, assets_path)

        host_port = self.container.ports[YAGNA_REST_PORT]
        proxy_ip = get_container_address(client, PROXY_HOST)
        self._api_base_host = YAGNA_REST_URL.substitute(host=proxy_ip, port=host_port)
        self._use_agent = config.use_requestor_agent

    # TODO: Consider making starting the agent independent from initialising
    # API clients: one may want to start an agent and still be able to make
    # API calls.
    def start_agent(self):
        """Start the requestor agent or initialize the API clients."""

        if self._use_agent:
            super().start_agent()
        else:
            self._init_activity_api(self._api_base_host)
            self._init_payment_api(self._api_base_host)
            self._init_market_api(self._api_base_host)
