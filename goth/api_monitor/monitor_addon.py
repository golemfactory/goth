"""Mitmproxy addon that traces API calls.

Verifies that a sequence of calls satisfies given properties.
"""
from __future__ import annotations
import logging
from typing import Dict, Optional

from mitmproxy.http import HTTPFlow, HTTPRequest

from goth.api_monitor.api_events import (
    APIEvent,
    APIRequest,
    APIResponse,
    APIError,
)
from goth.assertions.monitor import EventMonitor


class MonitorAddon:
    """This add-on keeps track of API requests and responses."""

    _monitor: EventMonitor[APIEvent]
    _pending_requests: Dict[HTTPRequest, APIRequest]
    _num_requests: int
    _logger: logging.Logger

    def __init__(self, monitor: Optional[EventMonitor[APIEvent]] = None):
        self._monitor = monitor or EventMonitor()
        if not self._monitor.is_running():
            self._monitor.start()
        self._pending_requests = {}
        self._num_requests = 0
        self._logger = logging.getLogger(__name__)

    def _register_event(self, event: APIEvent) -> None:
        """Log an API event and add it to the monitor."""

        self._logger.debug("%s", event)
        self._monitor.add_event_sync(event)

    def request(self, flow: HTTPFlow) -> None:
        """Register a request."""

        self._num_requests += 1
        request = APIRequest(self._num_requests, flow.request)
        self._pending_requests[flow.request] = request
        self._register_event(request)

    def response(self, flow: HTTPFlow) -> None:
        """Register a response."""

        request = self._pending_requests.get(flow.request)
        if request:
            assert flow.response is not None
            response = APIResponse(request, flow.response)
            del self._pending_requests[flow.request]
            self._register_event(response)
        else:
            self._logger.error("Received response for unregistered request: %s", flow)

    def error(self, flow: HTTPFlow) -> None:
        """Register an error."""

        request = self._pending_requests.get(flow.request)
        if request:
            assert flow.error is not None
            error = APIError(request, flow.error, flow.response)
            del self._pending_requests[flow.request]
            self._register_event(error)
        else:
            self._logger.error("Received error for unregistered request: %s", flow)
