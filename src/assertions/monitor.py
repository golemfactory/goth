"""
This module defines an event monitor class that registers events and checks
whether temporal assertions are satisfied.
"""

import asyncio
import importlib
import logging
from typing import Generic, List, Optional, Sequence

from src.assertions import Assertion, AssertionFunction, E, logger as assertions_logger

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s", level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


class EventMonitor(Generic[E]):
    """
    An event monitor registers *events* (values of type `E`) and manages *assertions*
    that specify properties of sequences of events. The assertions are evaluated
    with each new registered event.
    """

    assertions: List[Assertion[E]]
    """List of all assertions, active or finished"""

    _events: List[E]
    """List of events registered so far"""

    _worker_task: asyncio.Task
    """A worker task that registers events and checks assertions"""

    _incoming: "asyncio.Queue[Optional[E]]"
    """A queue used to pass the events to the worker task"""

    def __init__(self) -> None:
        self._events = []
        self._incoming = asyncio.Queue()
        self.assertions = []
        self._worker_task = None

    def add_assertions(self, assertion_funcs: List[AssertionFunction[E]]) -> None:
        """Add a list of assertion functions to this monitor."""

        self.assertions.extend(
            Assertion(self._events, func) for func in assertion_funcs
        )

    def load_assertions(self, module_name: str) -> None:
        """Load assertion functions from a module."""

        logger.info("Loading assertions from module '%s'", module_name)
        mod = importlib.import_module(module_name)
        assert mod is not None
        self.add_assertions(mod.__dict__["TEMPORAL_ASSERTIONS"])

    def start(self) -> None:
        """Start tracing events."""

        self._worker_task = asyncio.create_task(self._run_worker())

    def add_event(self, event: E) -> None:
        """Register a new event."""

        if not self.is_running():
            raise RuntimeError("Monitor is not running")

        self._incoming.put_nowait(event)

    async def stop(self) -> None:
        """Stop tracing events."""

        if self.is_running():
            # This will eventually terminate the worker task:
            self._incoming.put_nowait(None)
            await self._worker_task
            self._worker_task = None

    def is_running(self) -> bool:
        """Return `True` iff the monitor is accepting events."""

        return self._worker_task and not self._worker_task.done()

    def __del__(self) -> None:
        asyncio.create_task(self.stop())

    def __len__(self) -> int:
        """Return the number of registered events."""

        return len(self._events)

    async def _run_worker(self) -> None:
        """In a loop, register the incoming events and check the assertions."""

        for a in self.assertions:
            logger.debug("Starting assertion '%s'", a.name)
            a.start()

        events_ended = False

        while not events_ended:

            event = await self._incoming.get()

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
            # Ensure other tasks can also run between assertions
            await asyncio.sleep(0)

    @property
    def satisfied(self) -> Sequence[Assertion[E]]:
        """Return the satisfied assertions."""

        return [a for a in self.assertions if a.accepted]

    @property
    def failed(self) -> Sequence[Assertion[E]]:
        """Return the failed assertions."""

        return [a for a in self.assertions if a.failed]

    @property
    def done(self) -> Sequence[Assertion[E]]:
        """Return the completed assertions."""

        return [a for a in self.assertions if a.done]

    @property
    def finished(self) -> bool:
        """Return True iif all assertions are done."""

        for a in self.assertions:
            if not a.done:
                return False

        return True
