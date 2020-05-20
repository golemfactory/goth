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
from typing import Callable, Generic, List, Optional, TypeVar, Union

import src.assertions as assertions

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s", level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimerEvent:
    """A dummy event representing clock ticks, used for implementing timeouts"""

    timestamp: float


E = TypeVar("E")

EventOrTimer = Union[E, TimerEvent]

Assertion = assertions.Assertion[EventOrTimer]


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
    incoming: "queue.Queue[Optional[EventOrTimer]]"

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

    def add(self, event: EventOrTimer) -> None:
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

    def _instantiate_assertions(self) -> List[Assertion]:
        """Create assertion objects from assertion functions.

        Note: this must be done in the same thread that runs the asyncio loop.
        """
        asserts = []
        for func in self.assertion_funcs:
            a: Assertion = assertions.Assertion(self.events, func)
            logger.debug("Created assertion '%s'", a.name)
            asserts.append(a)

        return asserts

    async def _run_worker(self) -> None:
        """
        Run the thread that adds incoming requests/responses/errors
        to the trace and checks the properties
        """
        logger.info("Assertions thread started")

        asserts = self._instantiate_assertions()

        # Run the main assertions loop
        while not self.events_ended:

            event = self.incoming.get()

            if event is not None and not isinstance(event, TimerEvent):
                self.events.append(event)

            asserts = await self._check_assertions(asserts, event)

            if event is None:
                # `None` is used to signal the end of events
                self.events_ended = True

    async def _check_assertions(
        self, asserts: List[Assertion], event: Optional[EventOrTimer] = None
    ) -> List[Assertion]:

        active = []
        event_descr = (
            f"event #{len(self.events)}" if event is not None else "all events"
        )

        for a in asserts:

            if event is not None:
                await a.process_event(event)
            else:
                a.end_events()

            if a.accepted:
                assertions.logger.info(
                    "Assertion `%s` satisfied after %s", a.name, event_descr
                )
            elif a.failed:
                assertions.logger.error(
                    "Assertion `%s` failed after %s: %s", a.name, event_descr, a.result
                )
            else:
                active.append(a)

        return active
