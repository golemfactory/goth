"""This module defines an event monitor class.

that registers events and checks whether temporal assertions are satisfied.
"""

import asyncio
import importlib
import logging
from typing import Generic, List, Optional, Sequence

from goth.assertions import Assertion, AssertionFunction, E


class EventMonitor(Generic[E]):
    """An event monitor.

    That registers *events* (values of type `E`) and manages *assertions* that specify
    properties of sequences of events. The assertions are evaluated with each new
    registered event.
    """

    assertions: List[Assertion[E]]
    """List of all assertions, active or finished."""

    _events: List[E]
    """List of events registered so far."""

    _worker_task: Optional[asyncio.Task]
    """A worker task that registers events and checks assertions."""

    _incoming: "Optional[asyncio.Queue[Optional[E]]]"
    """A queue used to pass the events to the worker task."""

    _logger: logging.Logger

    def __init__(self, logger: Optional[logging.Logger] = None, on_stop=None) -> None:
        self._events = []
        # Delay creating the queue to make sure it's created in the event loop
        # used by the worker task.
        self._incoming = None
        self.assertions = []
        self._worker_task = None
        self._logger = logger or logging.getLogger(__name__)
        self._stop_callback = on_stop

    def add_assertion(self, assertion_func: AssertionFunction[E]) -> Assertion:
        """Add a list of assertion functions to this monitor."""

        result = Assertion(self._events, assertion_func)
        self.assertions.append(result)
        return result

    def add_assertions(self, assertion_funcs: List[AssertionFunction[E]]) -> None:
        """Add a list of assertion functions to this monitor."""

        # Create assertions here but don't start them yet, to make sure
        # they're started in the same event loop in which they'll be running.
        self.assertions.extend(
            Assertion(self._events, func) for func in assertion_funcs
        )

    def load_assertions(self, module_name: str) -> None:
        """Load assertion functions from a module."""

        self._logger.info("Loading assertions from module '%s'", module_name)
        mod = importlib.import_module(module_name)
        assert mod is not None
        self.add_assertions(mod.__dict__["TEMPORAL_ASSERTIONS"])

        # Set up the logger in the imported assertions module to use the handlers
        # used by `self._logger`.
        mod_logger = mod.__dict__.get("logger")
        if mod_logger and isinstance(mod_logger, logging.Logger):
            mod_logger.setLevel(self._logger.level)
            mod_logger.propagate = False
            for handler in self._logger.handlers:
                if handler not in mod_logger.handlers:
                    mod_logger.addHandler(handler)

    def start(self) -> None:
        """Start tracing events."""

        if self.is_running():
            self._logger.warning("Monitor already started")
            return

        self._incoming = asyncio.Queue()
        # Don't use `asyncio.create_task()` here, as it'll fail if the current
        # event loop is not running yet. `asyncio.ensure_future()` will create
        # a task which will be run when the loop is started.
        future = asyncio.ensure_future(self._run_worker())
        assert isinstance(future, asyncio.Task)
        self._worker_task = future
        self._logger.info("Monitor started")

    def add_event(self, event: E) -> None:
        """Register a new event."""

        if not self.is_running():
            raise RuntimeError("Monitor is not running")

        self._incoming.put_nowait(event)

    async def stop(self) -> None:
        """Stop tracing events."""

        if not self.is_running():
            self._logger.warning("Monitor already stopped")
            return

        self._logger.info("Stopping the monitor...")
        # This will eventually terminate the worker task:
        self._incoming.put_nowait(None)

        # Set `self._worker_task` to `None` so that when we'll be
        # waiting for the worker task to terminate, `self.is_running()`
        # will return `False` to prevent adding more events.
        worker = self._worker_task
        self._worker_task = None
        await worker
        self._logger.info("Monitor stopped")

        if not self.finished:
            # This may happen in case of ill-behaved assertions
            self._logger.error("Monitor stopped before all assertions finished")

        if self._stop_callback:
            self._stop_callback()

    def is_running(self) -> bool:
        """Return `True` iff the monitor is accepting events.

        If the worker thread has been terminated by an exception,
        this method re-raises the exception.
        """

        if not self._worker_task:
            return False

        if self._worker_task.done():
            if self._worker_task.exception():
                raise self._worker_task.exception()
            return False

        return True

    def __del__(self) -> None:

        if self.is_running():
            raise RuntimeError("Monitor is still running")

    async def _run_worker(self) -> None:
        """In a loop, register the incoming events and check the assertions."""

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

            # As new assertions may be added on the fly, we need to make sure
            # that this one has been started already.
            if not a.started:
                a.start()
                self._logger.debug("Assertion '%s' started", a.name)

            if a.done:
                continue

            await a.update_events(events_ended=events_ended)

            if a.accepted:
                msg = "Assertion '%s' succeeded after %s; result: %s"
                self._logger.info(msg, a.name, event_descr, str(a.result))

            elif a.failed:
                msg = "Assertion '%s' failed after %s; cause: %s"
                self._logger.error(msg, a.name, event_descr, str(a.result))

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

        return all(a.done for a in self.assertions)
