"""This module defines `APIMonitor` class that registers API calls and checks
whether temporal assertions are satisfied.
"""

# from __future__ import annotations
import asyncio
import importlib
import logging
import queue
import threading
from typing import Callable, Generic, List, Optional, Sequence, TypeVar

from src.assertions import Assertion, logger as assertions_logger

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s", level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


E = TypeVar("E")
"""Type of events"""


class EventMonitor(Generic[E]):
    """
    An event monitor registers *events* (values of type `E`) and manages *assertions*
    that specify properties of sequences of events. The assertions are evaluated
    with each new registered event.
    """

    _events: List[E]
    """List of API calls registered so far"""

    _worker_thread: threading.Thread
    """A worker thread that registers events and checks assertions"""

    _incoming: "queue.Queue[Optional[E]]"
    """A queue used to pass the events to the worker thread"""

    assertions: List[Assertion[E]]
    """List of all assertions (including the satisfied or failed ones)"""

    def __init__(self):
        self._events = []
        self._incoming = queue.Queue()
        self.assertions = []
        self.worker_thread = threading.Thread(
            target=lambda: asyncio.run(self._run_worker()),
            name="AssertionsThread",
            daemon=True,
        )

    def add_assertions(self, assertion_funcs: List[Callable]) -> None:
        """Add a list of assertion functions to this monitor"""

        self.assertions.extend(
            Assertion(self._events, func) for func in assertion_funcs
        )

    def load_assertions(self, module_name: str) -> None:
        """Load assertion functions from a module"""

        # We cannot instantiate `Assertion` objects here, since they will be
        # running in an asyncio event loop associated with another thread
        # (the worker thread). Hence we store the coroutine functions now and
        # create `Assertion` objects for them later on in the worker thread.
        logger.info("Loading assertions from module '%s'", module_name)
        mod = importlib.import_module(module_name)
        assert mod is not None
        self.add_assertions(mod.__dict__["TEMPORAL_ASSERTIONS"])

    def start(self) -> None:
        """Start tracing events"""

        self.worker_thread.start()

    def add_event(self, event: E) -> None:
        """Register a new HTTP request/response/error"""

        self._incoming.put(event)

    def stop(self) -> None:
        """Stop tracing events"""

        # This will eventually terminate the worker thread:
        self._incoming.put(None)
        self.worker_thread.join()

    def __del__(self) -> None:
        self.stop()

    def __len__(self) -> int:
        """Return the number of registered events"""

        return len(self._events)

    async def _run_worker(self) -> None:
        """In a loop, register the incoming events and check the assertions"""

        for a in self.assertions:
            logger.debug("Starting assertion '%s'", a.name)
            await a.start()

        events_ended = False

        while not events_ended:

            event = self._incoming.get()

            if event is not None:
                self._events.append(event)
            else:
                # `None` is used to signal the end of events
                events_ended = True

            await self._check_assertions(events_ended)

    async def _check_assertions(self, events_ended: bool) -> None:

        event_descr = (
            f"event #{len(self._events)}" if not events_ended else "all events"
        )

        for a in self.assertions:

            if a.done:
                continue

            await a.update_events(events_ended=events_ended)

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

    @property
    def satisfied(self) -> Sequence[Assertion[E]]:
        """Return the satified assertions."""

        return [a for a in self.assertions if a.accepted]

    @property
    def failed(self) -> Sequence[Assertion[E]]:
        """Return the failed assertions."""

        return [a for a in self.assertions if a.failed]
