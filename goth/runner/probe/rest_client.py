"""Module containing classes related to the yagna REST API client."""
import dataclasses
import logging
from typing import TypeVar

from typing_extensions import Protocol

import ya_activity
import ya_market
import ya_payment

from goth.address import (
    ensure_no_trailing_slash,
    ACTIVITY_API_URL,
    MARKET_API_URL,
    PAYMENT_API_URL,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ActivityApiClient:
    """
    Client for the activity API of a Yagna daemon.

    The activity API is divided into two domains: control and state. This division is
    reflected in the inner client objects of this class.
    """

    control: ya_activity.RequestorControlApi
    """Client for the control part of the activity API."""

    state: ya_activity.RequestorStateApi
    """Client for the state part of the activity API."""


class ConfigurationProtocol(Protocol):
    """Protocol representing the `Configuration` field of a given REST API module."""

    access_token: str


ConfTVar = TypeVar("ConfTVar", bound=ConfigurationProtocol)
ClientTVar = TypeVar("ClientTVar", covariant=True)


class ApiModule(Protocol[ConfTVar, ClientTVar]):
    """Representation of a REST API module.

    Used for typing `YagnaApiModule._create_api_client`.
    """

    def Configuration(self, host: str) -> ConfTVar:
        """Config instance for this API module."""
        pass

    def ApiClient(self, conf: ConfTVar) -> ClientTVar:
        """Client instance for this API module."""
        pass


class RestApiComponent:
    """Component with clients for all three yagna REST APIs."""

    activity: ActivityApiClient
    """Activity API client for the requestor daemon."""

    market: ya_market.RequestorApi
    """Market API client for the requestor daemon."""

    payment: ya_payment.RequestorApi
    """Payment API client for the requestor daemon."""

    _app_key: str

    def __init__(self, base_hostname: str, app_key: str):
        self._app_key = app_key
        self._init_activity_api(base_hostname)
        self._init_payment_api(base_hostname)
        self._init_market_api(base_hostname)

    def _create_api_client(
        self, api_module: ApiModule[ConfTVar, ClientTVar], api_url: str
    ) -> ClientTVar:
        api_url = ensure_no_trailing_slash(str(api_url))
        config: ConfTVar = api_module.Configuration(api_url)
        config.access_token = self._app_key
        return api_module.ApiClient(config)

    def _init_activity_api(self, api_base_host: str) -> None:
        api_url = ACTIVITY_API_URL.substitute(base=api_base_host)
        client = self._create_api_client(ya_activity, api_url)
        control = ya_activity.RequestorControlApi(client)
        state = ya_activity.RequestorStateApi(client)
        self.activity = ActivityApiClient(control, state)
        logger.debug("activity API initialized. url=%s", api_url)

    def _init_market_api(self, api_base_host: str) -> None:
        api_url = MARKET_API_URL.substitute(base=api_base_host)
        client = self._create_api_client(ya_market, api_url)
        self.market = ya_market.RequestorApi(client)
        logger.debug("market API initialized. url=%s", api_url)

    def _init_payment_api(self, api_base_host: str) -> None:
        api_url = PAYMENT_API_URL.substitute(base=api_base_host)
        client = self._create_api_client(ya_payment, api_url)
        self.payment = ya_payment.RequestorApi(client)
        logger.debug("payment API initialized. url=%s", api_url)
