"""Classes representing API calls and utility functions."""

import abc
import json
import re
from typing import Optional, Type

from mitmproxy.flow import Error
from mitmproxy.http import HTTPRequest, HTTPResponse

from goth.api_monitor.router_addon import CALLER_HEADER, CALLEE_HEADER


class APIEvent(abc.ABC):
    """Abstract superclass of API event classes."""

    @property
    @abc.abstractmethod
    def timestamp(self) -> float:
        """Return event's time."""

    @property
    @abc.abstractmethod
    def content(self) -> str:
        """Return the content of this event.

        For a request/response event, it's the request/response body.
        For an error event, it's the error message.
        """


class APIRequest(APIEvent):
    """Represents an API request."""

    number: int
    http_request: HTTPRequest

    def __init__(self, number: int, http_request: HTTPRequest):
        self.number = number
        self.http_request = http_request

    @property
    def timestamp(self) -> float:
        """Start time op the `http_request`."""
        return self.http_request.timestamp_start

    @property
    def method(self) -> str:
        """Return the method of the underlying HTTP request."""

        return self.http_request.method

    @property
    def path(self) -> str:
        """Return the method of the underlying HTTP request."""

        return self.http_request.path

    @property
    def caller(self) -> Optional[str]:
        """Return the caller name."""
        return self.http_request.headers.get(CALLER_HEADER)

    @property
    def callee(self) -> Optional[str]:
        """Return the callee name."""
        return self.http_request.headers.get(CALLEE_HEADER)

    @property
    def content(self) -> str:
        """Return the request body."""
        return self.http_request.content.decode("utf-8")

    @property
    def header_str(self) -> str:
        """Return the string representation of this request without the body."""
        return f"{self.caller} -> {self.callee}: {self.method} {self.path}"

    def __str__(self) -> str:
        return f"[request] {self.header_str}; body: {self.content}"


class APIResponse(APIEvent):
    """Represents a response to an API request."""

    request: APIRequest
    http_response: HTTPResponse

    def __init__(self, request: APIRequest, http_response: HTTPResponse):
        self.request = request
        self.http_response = http_response

    @property
    def timestamp(self) -> float:
        """Start time op the `http_response`."""
        return self.http_response.timestamp_start

    @property
    def status_code(self) -> int:
        """Return the HTTP status code."""

        return self.http_response.status_code

    @property
    def content(self) -> str:
        """Return the response body."""
        return self.http_response.content.decode("utf-8")

    def __str__(self) -> str:
        return (
            f"[response ({self.status_code})] "
            f"{self.request.header_str}; body: {self.content}"
        )


class APIError(APIEvent):
    """Represents an error when making an API request or sending a response."""

    request: APIRequest
    error: Error
    http_response: Optional[HTTPResponse]

    def __init__(
        self,
        request: APIRequest,
        error: Error,
        http_response: Optional[HTTPResponse] = None,
    ):
        self.request = request
        self.error = error
        self.http_reponse = http_response

    @property
    def timestamp(self) -> float:
        """Time of the error."""
        return self.error.timestamp

    @property
    def content(self) -> str:
        """Return self."""
        return self.error.msg

    def __str__(self) -> str:
        return f"[error] {self.request.header_str}: {self.content}"


def _match_event(
    event: APIEvent,
    event_class: Type[APIEvent],
    method: Optional[str] = None,
    path_regex: Optional[str] = None,
) -> bool:

    http_request: HTTPRequest
    if isinstance(event, APIRequest):
        http_request = event.http_request
    elif isinstance(event, (APIResponse, APIError)):
        http_request = event.request.http_request
    else:
        return False

    return (
        isinstance(event, event_class)
        and (method is None or http_request.method == method)
        and (path_regex is None or re.search(path_regex, http_request.path) is not None)
    )


def is_create_agreement_request(event: APIEvent) -> bool:
    """Check if `event` is a request of CreateAgreement operation."""

    return _match_event(event, APIRequest, "POST", "^/market-api/v1/agreements$")


def is_collect_demands_request(event: APIEvent, sub_id: str = "") -> bool:
    """Check if `event` is a request of CollectDemants operation."""

    sub_id_re = sub_id if sub_id else "[^/]+"
    return _match_event(
        event, APIRequest, "GET", f"^/market-api/v1/offers/{sub_id_re}/events"
    )


def is_subscribe_offer_request(event: APIEvent) -> bool:
    """Check if `event` is a request of SubscribeOffer operation."""

    return _match_event(event, APIRequest, "POST", "^/market-api/v1/offers$")


def is_unsubscribe_offer_request(event: APIEvent, sub_id: str = "") -> bool:
    """Check if `event` is a request of UnsubscribeOffer operation."""

    sub_id_re = sub_id if sub_id else "[^/]+"
    return _match_event(
        event, APIRequest, "DELETE", f"^/market-api/v1/offers/{sub_id_re}$"
    )


def is_subscribe_offer_response(event: APIEvent) -> bool:
    """Check if `event` is a response of SubscribeOffer operation."""

    return _match_event(event, APIResponse, "POST", "^/market-api/v1/offers$")


def is_invoice_send_response(event: APIEvent) -> bool:
    """Check if `event` is a response for InvoiceSend operation."""

    return _match_event(
        event, APIResponse, "POST", "^/payment-api/v1/provider/invoices/.*/send$"
    )


def get_response_json(event: APIEvent):
    """If `event` is a response then parse and return the included JSON.

    Otherwise return `None`.
    """

    if isinstance(event, APIResponse):
        return json.loads(event.http_response.text)

    return None


def get_activity_id_from_create_response(event: APIEvent) -> Optional[str]:
    """Look for the CreateActivity event to return the ActivityID.

    If `event` is a response to CreateActivity operation then return the activity ID
    included in the response. Otherwise return `None`.
    """

    if (
        isinstance(event, APIResponse)
        and event.request.method == "POST"
        and event.request.path == "/activity-api/v1/activity"
    ):
        return event.http_response.text.strip()[1:-1]

    return None


def get_activity_id_from_delete_response(event: APIEvent) -> Optional[str]:
    """If `event` is a response of DeleteActivity then return the included activity ID.

    Otherwise return `None`.
    """

    if (
        isinstance(event, APIRequest)
        and event.method == "DELETE"
        and event.path.startswith("/activity-api/v1/activity/")
    ):
        return event.path.rsplit("/", 1)[-1]

    return None
