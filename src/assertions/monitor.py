"""This module defines `APIMonitor` class that registers API calls and checks
whether temporal assertions are satisfied.
"""
from __future__ import annotations
import asyncio
import importlib
import logging
import queue
import threading
from typing import Callable, Generic, List, Optional, TypeVar

from src.assertions import Assertion, logger as assertions_logger

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s", level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


E = TypeVar("E")


class EventMonitor(Generic[E]):
    """
    Represents a sequence of API calls and a set of properties
    that the sequence has to satisfy.

    Since adding a new request to the sequence may trigger checking
    if all properties are satified, every instance of this class
    starts a separate thread that performs all the checks without
    blocking the client.
    """

    # List of API calls registered so far
    events: List[E]

    # Calls to register are taken from this queue
    incoming: "queue.Queue[Optional[E]]"

    # List of assertion functions to be instantiated by the worker thread
    assertion_funcs: List[Callable]  # Assertion[APIEvent]]

    # Flag set to signal that no further events will be emitted
    events_ended: bool

    def __init__(self):
        self.events = []
        self.incoming = queue.Queue()
        self.assertion_funcs = []
        self.events_ended = False

    def add_assertions(self, assertion_funcs: List[Callable]) -> None:
        """Add a list of assertion functions to this monitor"""
        self.assertion_funcs.extend(assertion_funcs)

    def load_assertions(self, module_name: str) -> None:
        """Load assertion functions from a module"""
        logger.info("Loading assertions from module '%s'", module_name)
        mod = importlib.import_module(module_name)
        assert mod is not None
        self.add_assertions(mod.__dict__["TEMPORAL_ASSERTIONS"])

    def start(self) -> None:
        """Start tracing events"""

        worker_thread = threading.Thread(
            target=lambda: asyncio.run(self._run_worker()),
            name="AssertionsThread",
            daemon=True,
        )
        # timer_thread = threading.Thread(
        #    target=self._timer_events, name="TimerThread", daemon=True
        # )

        worker_thread.start()
        # timer_thread.start()
        logger.info("Tracing started")

    def add(self, event: E) -> None:
        """Register a new HTTP request/response/error"""
        self.incoming.put(event)

    def stop(self) -> None:
        """Stop tracing events"""

        # This will eventually terminate the worker thread:
        self.events_ended = True
        self.incoming.put(None)

    def __del__(self) -> None:
        self.stop()

    def __len__(self) -> int:
        """Return the number of registered calls"""
        return len(self.events)

    # def _timer_events(self) -> None:

    #     while not self.events_ended:
    #         time.sleep(1.0)
    #         self.add(ClockTick(time.time()))

    def _instantiate_assertions(self) -> List[Assertion[E]]:
        """Create assertion objects from assertion functions.

        Note: this must be done in the same thread that runs the asyncio loop.
        """
        assertions = []
        for func in self.assertion_funcs:
            a: Assertion[E] = Assertion(self.events, func)
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

            if event is not None:
                self.events.append(event)
            else:
                # `None` is used to signal the end of events
                self.events_ended = True

            assertions = await self._check_assertions(assertions)

    async def _check_assertions(self, assertions: List[Assertion]) -> List[Assertion]:

        active = []
        event_descr = (
            f"event #{len(self.events)}" if not self.events_ended else "all events"
        )

        for a in assertions:
            await a.update_events(events_ended=self.events_ended)

            if a.accepted:
                assertions_logger.info(
                    "Assertion `%s` satisfied after %s, result: %s",
                    a.name,
                    event_descr,
                    a.result,
                )
            elif a.failed:
                assertions_logger.error(
                    "Assertion `%s` failed after %s: %s", a.name, event_descr, a.result
                )
            else:
                active.append(a)

        return active
