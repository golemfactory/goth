"""This module defines `APIMonitor` class that registers API calls and checks
whether temporal assertions are satisfied.
"""
from __future__ import annotations
import asyncio
import importlib
import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, Union

from api_events import APICall, APIError, APIEvent, APIResult
from assertions import Assertion
from assertions import logger as assertions_logger


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s", level=logging.DEBUG,
)

# `mitmproxy` adds ugly prefix to add-on module names
logger = logging.getLogger(__name__)  #  .replace("__mitmproxy_script__.", ""))

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


@dataclass(frozen=True)
class TimerEvent:
    """A dummy event representing clock ticks, used for implementing timeouts"""

    timestamp: float

    # def __init__(self, timestamp: float) -> None:
    #     self.timestamp = timestamp


APIorTimerEvent = Union[APIEvent, TimerEvent]

APIAssertion = Assertion[Union[APIEvent, TimerEvent]]  # APIorTimerEvent]


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
    incoming: "queue.Queue[Optional[APIorTimerEvent]]"

    # List of assertion functions to be instantiated by the worker thread
    assertion_funcs: List[Callable]  # Assertion[APIEvent]]

    # Flag set to signal that no further events will be emitted
    events_ended: bool

    def __init__(self):
        self.events = []
        self.incoming = queue.Queue()
        self.assertion_funcs = []
        self.events_ended = False

    def load_assertions(self, module_name: str) -> None:
        """Load assertion functions from a module"""
        logger.info("Loadin assertions from module '%s'", module_name)
        mod = importlib.import_module(module_name)
        assert mod is not None
        self.assertion_funcs.extend(mod.__dict__["TEMPORAL_ASSERTIONS"])

    def start(self) -> None:
        """Start tracing API calls"""

        worker_thread = threading.Thread(
            target=lambda: asyncio.run(self._run_worker()),
            name="AssertionsThread",
            daemon=True,
        )
        timer_thread = threading.Thread(
            target=self._timer_events, name="TimerThread", daemon=True
        )

        worker_thread.start()
        timer_thread.start()
        logger.info("Tracing started")

    def add(self, event: APIorTimerEvent) -> None:
        """Register a new HTTP request/response/error"""
        self.incoming.put(event)

    def __del__(self) -> None:
        # This will eventually terminate the worker thread:
        self.events_ended = True
        self.incoming.put(None)

    def __len__(self) -> int:
        """Return the number of registered calls"""
        return len(self.events)

    def _timer_events(self) -> None:

        while not self.events_ended:
            time.sleep(1.0)
            self.add(TimerEvent(time.time()))

    def _instantiate_assertions(self) -> List[APIAssertion]:
        """Create assertion objects from assertion functions.

        Note: this must be done in the same thread that runs the asyncio loop.
        """
        assertions = []
        for func in self.assertion_funcs:
            a: APIAssertion = Assertion(self.events, func)
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
        while not self.events_ended:

            event = self.incoming.get()

            if isinstance(event, APIEvent):
                self.events.append(event)
                _log_event(event)

            assertions = await self._check_assertions(assertions, event)

            if event is None:
                # `None` is used to signal the end of events
                self.events_ended = True

    async def _check_assertions(
        self, assertions: List[APIAssertion], event: Optional[APIorTimerEvent] = None
    ) -> List[APIAssertion]:

        active = []
        event_descr = (
            f"event #{len(self.events)}" if event is not None else "all events"
        )

        for a in assertions:

            if event is not None:
                await a.process_event(event)
            else:
                a.end_events()

            if a.accepted:
                assertions_logger.debug("Satisfied after %s: %s", event_descr, a.name)
            elif a.failed:
                assertions_logger.debug("Failed after %s: %s", event_descr, a.name)
                raise AssertionError(f"Assertion '{a.name}' failed: {a.result}")
            else:
                active.append(a)

        return active
