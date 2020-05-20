"""
Mitmproxy addon that traces API calls and verifies
that the sequence of calls satifies given properties
"""
from __future__ import annotations
import logging
from typing import Dict, Optional

import mitmproxy
from mitmproxy.http import HTTPFlow, HTTPRequest

from api_events import APICall, APIResult, APIError
from api_monitor import APIMonitor


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s", level=logging.DEBUG,
)

# `mitmproxy` adds ugly prefix to add-on module names
logger = logging.getLogger(__name__.replace("__mitmproxy_script__.", ""))


class MonitorAddon:
    """This add-on keeps track of API calls"""

    monitor: APIMonitor
    pending_calls: Dict[HTTPRequest, APICall]
    num_calls: int

    def __init__(self):
        self.monitor = APIMonitor()
        self.pending_calls = {}
        self.num_calls = 0

    def load(self, loader):
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

    def request(self, flow: HTTPFlow) -> None:
        """Register a request"""

        self.num_calls += 1
        call = APICall(self.num_calls, flow.request)
        self.pending_calls[flow.request] = call
        self.monitor.add(call)

    def response(self, flow: HTTPFlow):
        """Register a response"""

        call = self.pending_calls.get(flow.request)
        if call:
            assert flow.response is not None
            response = APIResult(call, flow.response)
            del self.pending_calls[flow.request]
            self.monitor.add(response)
        else:
            logger.error("Received response for unregistered call: %s", flow)

    def error(self, flow: HTTPFlow):
        """Register an error"""

        call = self.pending_calls.get(flow.request)
        if call:
            assert flow.error is not None
            error = APIError(call, flow.error, flow.response)
            del self.pending_calls[flow.request]
            self.monitor.add(error)
        else:
            logger.error("Received error for unregistered call: %s", flow)


# This is used by mitmproxy to install add-ons
addons = [MonitorAddon()]
