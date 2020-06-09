"""
This module defines an event monitor class that registers events and checks
whether temporal assertions are satisfied.
"""

# from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
import importlib
import logging
import threading
from typing import Generic, List, Optional, Sequence

from src.assertions import Assertion, AssertionFunction, E, logger as assertions_logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

    _worker_thread: asyncio.Task
    """A worker task that registers events and checks assertions"""

    _incoming: "asyncio.Queue[Optional[E]]"
    """A queue used to pass the events to the worker task"""

    def __init__(self) -> None:
        self._events = []
        self._incoming = asyncio.Queue()
        self.assertions = []
        self._worker_thread = None

    def add_assertions(self, assertion_funcs: List[AssertionFunction[E]]) -> None:
        """Add a list of assertion functions to this monitor."""

        new_assertions = [Assertion(self._events, func) for func in assertion_funcs]
        self.assertions.extend(new_assertions)

        for a in new_assertions:
            a.start()

    def load_assertions(self, module_name: str) -> None:
        """Load assertion functions from a module."""

        # We cannot instantiate `Assertion` objects here, since they will be
        # running in an asyncio event loop associated with another thread
        # (the worker thread). Hence we store the coroutine functions now and
        # create `Assertion` objects for them later on in the worker thread.
        logger.info("Loading assertions from module '%s'", module_name)
        mod = importlib.import_module(module_name)
        assert mod is not None
        self.add_assertions(mod.__dict__["TEMPORAL_ASSERTIONS"])

    def start(self) -> None:
        """Start tracing events."""
        logger.debug("start()")

        self._worker_thread = asyncio.create_task(self._run_worker())

    async def add_event(self, event: E) -> None:
        """Register a new event."""
        logger.debug("add_event(%r)", event)
        if not self.is_running():
            raise RuntimeError("Monitor is not running")

        await self._incoming.put(event)

    async def await_assertions(self, timeout: timedelta = timedelta(seconds=10)):
        logger.debug("await_assertions()")

        if not self.is_running():
            raise RuntimeError("Monitor is not running")

        deadline = datetime.now() + timeout

        while not self.finished:
            if deadline < datetime.now():
                raise TimeoutError
            await asyncio.sleep(0.1)
        logger.debug("await_assertions() - finished")

    async def stop(self) -> None:
        """Stop tracing events."""

        if self.is_running():
            self._worker_thread.cancel()
            await self._worker_thread
            logger.debug("worker_thread stopped %s", self._worker_thread.done())
            self._worker_thread = None
        if not self.finished:
            logger.error("Monitor stopped before it was finished")

    def is_running(self) -> bool:
        """Return `True` iff the monitor is accepting events."""

        return self._worker_thread and not self._worker_thread.done()

    def __del__(self) -> None:
        asyncio.ensure_future(self.stop())

    def __len__(self) -> int:
        """Return the number of registered events."""

        return len(self._events)

    async def _run_worker(self) -> None:
        """In a loop, register the incoming events and check the assertions."""
        logger.debug("run_worker()")

        for a in self.assertions:
            logger.debug("Starting assertion '%s'", a.name)
            a.start()

        try:
            await self._check_events()
        except asyncio.CancelledError:
            return
        except RuntimeError as e:
            if not "Event loop is closed" in str(e):
                raise
            return

    async def _check_events(self):
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

    @property
    def satisfied(self) -> Sequence[Assertion[E]]:
        """Return the satified assertions."""

        return [a for a in self.assertions if a.accepted]

    @property
    def failed(self) -> Sequence[Assertion[E]]:
        """Return the failed assertions."""

        return [a for a in self.assertions if a.failed]

    @property
    def finished(self) -> bool:
        """Return True iif all assertions are done."""

        for a in self.assertions:
            if not a.done:
                return False

        return True
