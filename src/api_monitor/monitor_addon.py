"""
Mitmproxy addon that traces API calls and verifies
that the sequence of calls satifies given properties
"""
from __future__ import annotations
import asyncio
import importlib
import logging
import queue
import threading
from typing import Callable, Dict, List, Optional

import mitmproxy
from mitmproxy.http import HTTPFlow, HTTPRequest

from api_events import APICall, APIError, APIEvent, APIResult
from assertions import Assertion
from assertions import logger as assertions_logger


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s", level=logging.DEBUG,
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
    if isinstance(event, APICall):
        status = "in progress"
        call = event
    elif isinstance(event, APIResult):
        status = f"completed ({event.response.status_code})"
        call = event.call
    elif isinstance(event, APIError):
        status = "failed"
        call = event.call

    logger.info("%s:\t%s", call, status)

    call_logger.info(
        "%s:\t%s",
        event,
        status,
        extra={
            "num": call.number,
            "caller": call.caller,
            "callee": call.callee,
            "method": call.request.method,
            "path": call.request.path,
            "status": status,
        },
    )


class APIMonitor:
    """
    Represents a sequence of API calls and a set of properties
    that the sequence has to satisfy.

    Since adding a new request to the sequence may trigger checking
    if all properties are satified, every instance of this class
    starts a separate thread that performs all the checks without
    blocking the client.
    """

    # List of API calls registered so far
    events: List[APIEvent]

    # Calls to register are taken from this queue
    incoming: "queue.Queue[Optional[APIEvent]]"

    # All heavy work is done in a separate thread
    worker: threading.Thread

    # List of assertion functions to be instantiated by the worker thread
    assertion_funcs: List[Callable]  # Assertion[APIEvent]]

    def __init__(self):
        self.events = []
        self.incoming = queue.Queue()
        self.assertion_funcs = []
        self.worker = threading.Thread(
            target=lambda: asyncio.run(self._run_worker()),
            name="AssertionsThread",
            daemon=True,
        )

    def load_assertions(self, module_name: str) -> None:
        """Load assertion functions from a module"""
        mod = importlib.import_module(module_name)
        self.assertion_funcs.extend(mod.__dict__["TEMPORAL_ASSERTIONS"])

    def start(self) -> None:
        """Start tracing API calls"""
        self.worker.start()
        logger.info("Tracing started")

    def add(self, event: APIEvent) -> None:
        """Register a new HTTP request/response/error"""
        self.incoming.put(event)

    def __del__(self) -> None:
        # This will eventually terminate the worker thread:
        self.incoming.put(None)

    def __len__(self) -> int:
        """Return the number of registered calls"""
        return len(self.events)

    def _instantiate_assertions(self) -> List[Assertion[APIEvent]]:
        """Create assertion objects from assertion functions.

        Note: this must be done in the same thread that runs the asyncio loop.
        """
        assertions = []
        for func in self.assertion_funcs:
            a = Assertion(self.events, func)
            logger.debug("Created assertion '%s'", a.name)
            assertions.append(a)

        return assertions

    async def _run_worker(self) -> None:
        """
        Run the thread that adds incoming requests/responses/errors
        to the trace and checks the properties
        """
        logger.info("Assertions thread started")

        assertions = self._instantiate_assertions()

        # Run the main assertions loop
        while True:
            event = self.incoming.get()
            if event is None:
                # it's time to finish
                break

            self.events.append(event)
            _log_event(event)
            assertions = await self._check_assertions(assertions)

        for a in assertions:
            await a.end_events()

        # End of history reached! Check the remaining assertions.
        await self._check_assertions(assertions, at_end=True)

    async def _check_assertions(
        self, assertions: List[Assertion[APIEvent]], at_end: bool = False
    ) -> List[Assertion[APIEvent]]:

        active: List[Assertion[APIEvent]] = []
        event_descr = f"event #{len(self.events)}" if not at_end else "all events"

        for a in assertions:
            await a.process_event()
            if a.accepted:
                assertions_logger.debug("Satisfied after %s: %s", event_descr, a.name)
            elif a.failed:
                assertions_logger.debug("Failed after %s: %s", event_descr, a.name)
                raise AssertionError(str(a))
            else:
                active.append(a)

        return active


class TracerAddon:
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
            response = APIResult(call, flow.response)
            del self.pending_calls[flow.request]
            self.monitor.add(response)
        else:
            logger.error("Received response for unregistered call: %s", flow)

    def error(self, flow: HTTPFlow):
        """Register an error"""

        call = self.pending_calls.get(flow.request)
        if call:
            error = APIError(call, flow.error, flow.response)
            del self.pending_calls[flow.request]
            self.monitor.add(error)
        else:
            logger.error("Received error for unregistered call: %s", flow)


# This is used by mitmproxy to install add-ons
addons = [TracerAddon()]
