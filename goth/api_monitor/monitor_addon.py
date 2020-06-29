"""
Mitmproxy addon that traces API calls and verifies
that the sequence of calls satifies given properties
"""
from __future__ import annotations
import logging
import threading
import time
from typing import Dict, Optional

import mitmproxy.ctx
from mitmproxy.http import HTTPFlow, HTTPRequest

from goth.api_monitor.api_events import (
    APIEvent,
    APIClockTick,
    APIRequest,
    APIResponse,
    APIError,
)
from goth.assertions.monitor import EventMonitor


logging.basicConfig(
    format="[%(asctime)s %(levelname)s %(name)s] %(message)s", level=logging.DEBUG,
)

# `mitmproxy` adds ugly prefix to add-on module names
logger = logging.getLogger(__name__.replace("__mitmproxy_script__.", ""))

# Setup call logging to "calls.log" file
call_logger = logging.getLogger("api_calls")
_log_handler = logging.FileHandler("calls.log", mode="w")
_log_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(num)-4s %(status)-15s %(caller)-15s -> "
        "%(callee)-16s %(method)-6s %(path)s"
    )
)
call_logger.handlers = [_log_handler]
call_logger.propagate = False


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

    call_logger.info(
        "%s:\t%s",
        event,
        status,
        extra={
            "num": request.number,
            "caller": request.caller,
            "callee": request.callee,
            "method": request.method,
            "path": request.path,
            "status": status,
        },
    )


class MonitorAddon:
    """This add-on keeps track of API requests and responses"""

    monitor: EventMonitor[APIEvent]
    pending_requests: Dict[HTTPRequest, APIRequest]
    num_requests: int

    def __init__(self):
        self.monitor = EventMonitor()
        self.pending_requests = {}
        self.num_requests = 0

    def load(self, loader) -> None:
        """Load module with property functions"""

        loader.add_option(
            name="assertions",
            typespec=Optional[str],
            default=None,
            help="A file with the assertions to check",
        )
        mitmproxy.ctx.options.process_deferred()
        assertions_module = mitmproxy.ctx.options.assertions
        if assertions_module is not None:
            self.monitor.load_assertions(assertions_module)
        self.monitor.start()
        self.monitor.add_event(APIClockTick())

        timer_thread = threading.Thread(
            target=self._timer, name="Timer thread", daemon=True
        )
        timer_thread.start()

    def _timer(self) -> None:
        """Periodically emit `APIClockTick` event"""

        logger.debug("Timer thread started")
        while not self.monitor.is_running():
            self.monitor.add_event(APIClockTick())
            time.sleep(1.0)

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
