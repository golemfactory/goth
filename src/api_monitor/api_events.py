"""Classes representing API calls and utility functions"""
import abc
import json
import re
import time
from typing import Optional, Type

from mitmproxy.flow import Error
from mitmproxy.http import HTTPRequest, HTTPResponse

from src.api_monitor.router_addon import CALLER_HEADER, CALLEE_HEADER


class APIEvent(abc.ABC):
    """Abstract superclass of API event classes"""

    @property
    @abc.abstractmethod
    def timestamp(self) -> float:
        """Return event's time"""


class APIClockTick(APIEvent):
    """A dummy event representing clock ticks, used for timeouts in API monitor"""

    def __init__(self, timestamp: Optional[float] = None):
        self._timestamp = timestamp or time.time()

    @property
    def timestamp(self) -> float:
        return self._timestamp


class APICall(APIEvent):
    """Represents an API call"""

    number: int
    request: HTTPRequest

    def __init__(self, number: int, request: HTTPRequest):
        self.number = number
        self.request = request

    @property
    def timestamp(self) -> float:
        return self.request.timestamp_start

    @property
    def caller(self) -> Optional[str]:
        """Return the caller name"""
        return self.request.headers.get(CALLER_HEADER)

    @property
    def callee(self) -> Optional[str]:
        """Return the callee name"""
        return self.request.headers.get(CALLEE_HEADER)

    def __str__(self):
        return (
            f"{self.caller} -> {self.callee}.{self.request.method}"
            f"({self.request.path})"
        )


class APIResult(APIEvent):
    """Represents a response to an API call"""

    call: APICall
    response: HTTPResponse

    def __init__(self, call: APICall, response: HTTPResponse):
        self.call = call
        self.response = response

    @property
    def timestamp(self) -> float:
        return self.response.timestamp_start


class APIError(APIEvent):
    """Represents an error when making an API call or sending a response"""

    call: APICall
    error: Error
    response: Optional[HTTPResponse]

    def __init__(
        self, call: APICall, error: Error, response: Optional[HTTPResponse] = None,
    ):
        self.call = call
        self.error = error
        self.reponse = response

    @property
    def timestamp(self) -> float:
        return self.error.timestamp


def _match_event(
    event: APIEvent,
    event_class: Type[APIEvent],
    method: Optional[str] = None,
    path_regex: Optional[str] = None,
) -> bool:

    request: HTTPRequest
    if isinstance(event, APICall):
        request = event.request
    elif isinstance(event, (APIResult, APIError)):
        request = event.call.request
    else:
        return False

    return (
        isinstance(event, event_class)
        and (method is None or request.method == method)
        and (path_regex is None or re.search(path_regex, request.path) is not None)
    )


def is_import_key_call(event: APIEvent) -> bool:
    """Check if `event` is a call of ImportKey operation."""

    return _match_event(event, APICall, "POST", "^/admin/import-key$")


def is_create_agreement_call(event: APIEvent) -> bool:
    """Check if `event` is a call of CreateAgreement operation."""

    return _match_event(event, APICall, "POST", "^/market-api/v1/agreements$")


def is_collect_demands_call(event: APIEvent, sub_id: str = "") -> bool:
    """Check if `event` is a call of CollectDemants operation."""

    sub_id_re = sub_id if sub_id else "[^/]+"
    return _match_event(
        event, APICall, "GET", f"^/market-api/v1/offers/{sub_id_re}/events"
    )


def is_subscribe_offer_call(event: APIEvent) -> bool:
    """Check if `event` is a call of SubscribeOffer operation."""

    return _match_event(event, APICall, "POST", "^/market-api/v1/offers$")


def is_subscribe_offer_response(event: APIEvent) -> bool:
    """Check if `event` is a response of SubscribeOffer operation."""

    return _match_event(event, APIResult, "POST", "^/market-api/v1/offers$")


def get_response_json(event: APIEvent):
    """If `event` is a response then parse and return the included JSON.
    Otherwise return `None`."""

    if isinstance(event, APIResult):
        return json.loads(event.response.text)

    return None


def get_activity_id_from_create_response(event: APIEvent) -> Optional[str]:
    """If `event` is a response to CreateActivity operation then return the activity ID
    included in the response. Otherwise return `None`."""

    if (
        isinstance(event, APIResult)
        and event.call.request.method == "POST"
        and event.call.request.path == "/activity-api/v1/activity"
    ):
        return event.response.text.strip()[1:-1]

    return None


def get_activity_id_from_delete_call(event: APIEvent) -> Optional[str]:
    """If `event` is a call of DeleteActivity then return the included activity ID.
    Otherwise return `None`.
    """

    if (
        isinstance(event, APICall)
        and event.request.method == "DELETE"
        and event.request.path.startswith("/activity-api/v1/activity/")
    ):
        return event.request.path.rsplit("/", 1)[-1]

    return None
