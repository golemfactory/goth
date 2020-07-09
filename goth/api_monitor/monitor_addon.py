"""
Mitmproxy addon that traces API calls and verifies
that the sequence of calls satifies given properties
"""
from __future__ import annotations
import asyncio
import logging
from typing import Dict, Optional

from mitmproxy.http import HTTPFlow, HTTPRequest

from goth.api_monitor.api_events import (
    APIEvent,
    APIClockTick,
    APIRequest,
    APIResponse,
    APIError,
)
from goth.assertions.monitor import EventMonitor


logger = logging.getLogger(__name__)


def _log_event(event: APIEvent) -> None:
    if isinstance(event, APIRequest):
        status = "in progress"
        request = event
    elif isinstance(event, APIResponse):
        status = f"completed ({event.status_code})"
        request = event.request
    elif isinstance(event, APIError):
        status = "failed"
        request = event.request

    logger.info("%s:\t%s", request, status)


class MonitorAddon:
    """This add-on keeps track of API requests and responses"""

    monitor: EventMonitor[APIEvent]
    pending_requests: Dict[HTTPRequest, APIRequest]
    num_requests: int

    def __init__(self, monitor: Optional[EventMonitor[APIEvent]] = None):
        self.monitor = monitor or EventMonitor()
        self.pending_requests = {}
        self.num_requests = 0

    def load(self, _loader) -> None:
        """A callback called when this add-on is inserted into mitmproxy."""

        if not self.monitor.is_running():
            self.monitor.start()
        self.monitor.add_event(APIClockTick())

        asyncio.ensure_future(self._timer())

    async def _timer(self) -> None:
        """Periodically emit `APIClockTick` event"""

        logger.debug("Timer thread started")
        while self.monitor.is_running():
            self.monitor.add_event(APIClockTick())
            await asyncio.sleep(1.0)

    def _register_event(self, event: APIEvent) -> None:

        _log_event(event)
        self.monitor.add_event(event)

    def request(self, flow: HTTPFlow) -> None:
        """Register a request"""

        self.num_requests += 1
        request = APIRequest(self.num_requests, flow.request)
        self.pending_requests[flow.request] = request
        self._register_event(request)

    def response(self, flow: HTTPFlow) -> None:
        """Register a response"""

        request = self.pending_requests.get(flow.request)
        if request:
            assert flow.response is not None
            response = APIResponse(request, flow.response)
            del self.pending_requests[flow.request]
            self._register_event(response)
        else:
            logger.error("Received response for unregistered request: %s", flow)

    def error(self, flow: HTTPFlow) -> None:
        """Register an error"""

        request = self.pending_requests.get(flow.request)
        if request:
            assert flow.error is not None
            error = APIError(request, flow.error, flow.response)
            del self.pending_requests[flow.request]
            self._register_event(error)
        else:
            logger.error("Received error for unregistered request: %s", flow)


# This is used by mitmproxy to install add-ons
addons = [MonitorAddon()]
