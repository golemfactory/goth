"""Classes representing API calls and utility functions."""

import abc
import json
import re
from typing import Any, Dict, Optional, Type, Union

from mitmproxy.flow import Error
from mitmproxy.http import HTTPRequest, HTTPResponse

from goth.api_monitor.router_addon import AGENT_HEADER, NODE_HEADER


class APIEvent(abc.ABC):
    """Abstract superclass of API event classes."""

    request: "APIRequest"
    """The request event associated with this event."""

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
        self.request = self
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
        """Return the caller name. Deprecated, use `agent_name()` instead."""
        return self.http_request.headers.get(AGENT_HEADER)

    @property
    def callee(self) -> Optional[str]:
        """Return the callee name. Deprecated, use `node_name()` instead."""
        return self.http_request.headers.get(NODE_HEADER)

    @property
    def agent_name(self) -> str:
        """Return the name of the agent from which the request originates."""
        return self.http_request.headers[AGENT_HEADER]

    @property
    def node_name(self) -> str:
        """Return the name of the yagna node to which the request is made."""
        return self.http_request.headers[NODE_HEADER]

    @property
    def content(self) -> str:
        """Return the request body."""
        return self.http_request.content.decode("utf-8")

    @property
    def header_str(self) -> str:
        """Return the string representation of this request without the body."""
        return f"{self.agent_name} -> {self.node_name}: {self.method} {self.path}"

    def __str__(self) -> str:
        return f"[request] {self.header_str}; body: {self.content}"


class APIResponse(APIEvent):
    """Represents a response to an API request."""

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


def get_response_json(event: APIEvent) -> Any:
    """If `event` is a response then parse and return the included JSON.

    Otherwise return `None`.
    """

    if isinstance(event, APIResponse):
        return json.loads(event.http_response.text)

    return None


MatchResult = Union[bool, Dict[str, str]]


def match_event(
    event: APIEvent,
    *,
    event_type: Type[APIEvent],
    agent_name: Optional[str] = None,
    node_name: Optional[str] = None,
    method: Optional[str] = None,
    path_regex: Optional[str] = None,
) -> MatchResult:
    """Check if `event` matches given condition.

    If not all conditions are satifised, returns `False`.

    If all conditions are satisfied, `path_regex` is defined and matching
    against `path_regex` produces an object `match: re.Match` with nonempty
    `match.groupdict()` then `mathch.groupdict()` is returned.

    Otherwise, returns `True`.
    """

    http_request = event.request.http_request

    if not isinstance(event, event_type):
        return False

    if agent_name and event.request.agent_name != agent_name:
        return False

    if node_name and event.request.node_name != node_name:
        return False

    if method and http_request.method != method:
        return False

    if not path_regex:
        return True

    match = re.search(path_regex, http_request.path)
    if not match:
        return False

    return match.groupdict() or True


# Market API

PARAM_REGEX = "[^/?]+"


def is_agreement_events(
    event: APIEvent,
    **kwargs,
) -> MatchResult:
    """Check if `event` is associated with AgreementEvents operation."""

    return match_event(
        event,
        method="GET",
        path_regex=r"^/market-api/v1/agreementEvents($|\?)",
        **kwargs,
    )


def is_approve_agreement(
    event: APIEvent,
    *,
    agr_id: str = PARAM_REGEX,
    **kwargs,
) -> MatchResult:
    """Check if `event` is associated with ApproveAgreement operation."""

    return match_event(
        event,
        method="POST",
        path_regex=fr"^/market-api/v1/agreements/(?P<agr_id>{agr_id})/approve($|\?)",
        **kwargs,
    )


def is_collect_demands(
    event: APIEvent,
    *,
    sub_id: str = PARAM_REGEX,
    **kwargs,
) -> MatchResult:
    """Check if `event` is associated with CollectDemands operation."""

    return match_event(
        event,
        method="GET",
        path_regex=fr"^/market-api/v1/offers/(?P<sub_id>{sub_id})/events($|\?)",
        **kwargs,
    )


def is_counter_proposal_offer(
    event: APIEvent,
    *,
    sub_id: str = PARAM_REGEX,
    prop_id: str = PARAM_REGEX,
    **kwargs,
) -> MatchResult:
    """Check if `event` is associated with CounterProposalOffer operation."""

    return match_event(
        event,
        method="POST",
        path_regex=(
            fr"^/market-api/v1/offers/(?P<sub_id>{sub_id})"
            fr"/proposals/(?P<prop_id>{prop_id})($|\?)"
        ),
        **kwargs,
    )


def is_create_agreement(event: APIEvent, **kwargs) -> MatchResult:
    """Check if `event` is associated with a CreateAgreement operation."""

    return match_event(
        event, method="POST", path_regex=r"^/market-api/v1/agreements($|\?)", **kwargs
    )


def is_subscribe_offer(event: APIEvent, **kwargs) -> MatchResult:
    """Check if `event` is associated with SubscribeOffer operation."""

    return match_event(
        event, method="POST", path_regex=r"^/market-api/v1/offers($|\?)", **kwargs
    )


def is_unsubscribe_offer(
    event: APIEvent, *, sub_id: str = PARAM_REGEX, **kwargs
) -> MatchResult:
    """Check if `event` is associated with UnsubscribeOffer operation."""

    return match_event(
        event,
        method="DELETE",
        path_regex=fr"^/market-api/v1/offers/(?P<sub_id>{sub_id})($|\?)",
        **kwargs,
    )


# Payment API


def is_get_invoice_events(event: APIEvent, **kwargs) -> MatchResult:
    """Check if `event` is associated with GetInvoiceEvents operation."""

    return match_event(
        event,
        method="GET",
        path_regex=r"^/payment-api/v1/invoiceEvents($|\?)",
        **kwargs,
    )


def is_issue_debit_note(event: APIEvent, **kwargs) -> MatchResult:
    """Check if `event` is associated with a IssueDebitNote operation."""

    return match_event(
        event, method="POST", path_regex=r"^/payment-api/v1/debitNotes($|\?)", **kwargs
    )


def is_send_debit_note(
    event: APIEvent, note_id: str = PARAM_REGEX, **kwargs
) -> MatchResult:
    """Check if `event` is associated with a SendDebitNote operation."""

    return match_event(
        event,
        method="POST",
        path_regex=fr"^/payment-api/v1/debitNotes/{note_id}/send($|\?)",
        **kwargs,
    )


def is_send_invoice(
    event: APIEvent, *, inv_id: str = PARAM_REGEX, **kwargs
) -> MatchResult:
    """Check if `event` is associated with SendInvoice operation."""

    return match_event(
        event,
        method="POST",
        path_regex=fr"^/payment-api/v1/invoices/(?P<inv_id>{inv_id})/send($|\?)",
        **kwargs,
    )


def contains_agreement_terminated_event(
    event: APIEvent,
    *,
    agr_id: Optional[str] = None,
    **kwargs,
) -> Optional[Dict[str, str]]:
    """Check if `event` is AgreementEvents response with AgreementTerminatedEvent."""

    if is_agreement_events(event, event_type=APIResponse, **kwargs):
        events = get_response_json(event)
        for agr_event in events:
            if agr_event.get("eventtype") == "AgreementTerminatedEvent" and (
                not agr_id or agr_event.get("agreementId") == agr_id
            ):
                return agr_event
    return None
