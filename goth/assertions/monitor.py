"""This module defines an event monitor class.

that registers events and checks whether temporal assertions are satisfied.
"""

import asyncio
from collections import OrderedDict
import importlib
import logging
import sys
from typing import Callable, Generic, List, Optional, Sequence, Union

from goth.assertions import Assertion, AssertionFunction, E


class MonitorLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter adding monitor name to each log message."""

    EXTRA_MONITOR_NAME = "monitor_name"

    _base_logger: logging.Logger

    def __init__(self, base_logger: logging.Logger, *args):
        super().__init__(base_logger, *args)
        self._base_logger = base_logger

    def process(self, msg, kwargs):
        """Process the log message `msg`."""
        return ("[%s] %s" % (self.extra[self.EXTRA_MONITOR_NAME], msg), kwargs)

    @property
    def handlers(self) -> List[logging.Handler]:
        """Return the handlers of the base logger."""
        return self._base_logger.handlers


LogLevel = int


class EventMonitor(Generic[E]):
    """An event monitor.

    That registers *events* (values of type `E`) and manages *assertions* that specify
    properties of sequences of events. The assertions are evaluated with each new
    registered event.
    """

    assertions: "OrderedDict[Assertion[E], LogLevel]"
    """List of all assertions, active or finished.

    For each assertion we also store the log level to be used
    for logging a message when this assertion succeeds.
    """

    name: Optional[str]
    """The name of this monitor, for use in logging."""

    _event_loop: asyncio.AbstractEventLoop
    """The event loop in which this monitor has been started."""

    _events: List[E]
    """List of events registered so far."""

    _incoming: "asyncio.Queue[Optional[E]]"
    """A queue used to pass the events to the worker task."""

    _last_checked_event: int
    """The index of the last event examined by `wait_for_event()` method.

    Subsequent calls to `wait_for_event` will only look at events that occurred
    after this event.
    """

    _logger: Union[logging.Logger, MonitorLoggerAdapter]
    """A logger instance for this monitor."""

    _worker_task: Optional[asyncio.Task]
    """A worker task that registers events and checks assertions."""

    def __init__(
        self,
        name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        on_stop=None,
    ) -> None:
        self.assertions = OrderedDict()
        self.name = name

        self._event_loop = asyncio.get_event_loop()
        self._events = []
        self._incoming = asyncio.Queue()
        self._last_checked_event = -1
        self._logger = logger or logging.getLogger(__name__)
        if self.name:
            self._logger = MonitorLoggerAdapter(
                self._logger, {MonitorLoggerAdapter.EXTRA_MONITOR_NAME: self.name}
            )
        self._stop_callback = on_stop
        self._worker_task = None

    def add_assertion(
        self, assertion_func: AssertionFunction[E], log_level: LogLevel = logging.INFO
    ) -> Assertion:
        """Add an assertion function to this monitor."""

        assertion = Assertion(self._events, assertion_func)
        assertion.start()
        self._logger.debug("Assertion '%s' started", assertion.name)
        self.assertions[assertion] = log_level
        return assertion

    def add_assertions(self, assertion_funcs: List[AssertionFunction[E]]) -> None:
        """Add a list of assertion functions to this monitor."""

        for func in assertion_funcs:
            self.add_assertion(func)

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
            mod_logger.setLevel(self._logger.getEffectiveLevel())
            mod_logger.propagate = False
            for handler in self._logger.handlers:
                if handler not in mod_logger.handlers:
                    mod_logger.addHandler(handler)

    def start(self) -> None:
        """Start tracing events.

        Starting a monitor is decoupled from its initialisation. This allows the
        user to add assertions to the monitor before starting to register events.
        Such assertions are thus guaranteed not to "miss" any event registered
        by the monitor.
        """

        if self.is_running():
            self._logger.warning("Monitor already started")
            return

        self._worker_task = self._event_loop.create_task(self._run_worker())
        self._logger.debug("Monitor started")

    async def add_event(self, event: E) -> None:
        """Register a new event."""

        # Note: this method is `async` even though it does not perform any `await`.
        # This is to ensure that it's directly callable only from code running in
        # an event loop, which in turn guarantees that tasks waiting for input from
        # `self._incoming` will be notified.

        if not self.is_running():
            raise RuntimeError(f"Monitor {self.name or ''} is not running")

        self._incoming.put_nowait(event)

    def add_event_sync(self, event: E) -> None:
        """Schedule registering a new event.

        This function can be called from a thread different from the one
        that started this monitor.
        """

        if not self.is_running():
            raise RuntimeError(f"Monitor {self.name or ''} is not running")

        self._event_loop.call_soon_threadsafe(self._incoming.put_nowait, event)

    async def stop(self) -> None:
        """Stop tracing events."""

        if not self.is_running():
            self._logger.warning("Monitor already stopped")
            return

        self._logger.debug("Stopping the monitor...")
        # This will eventually terminate the worker task:
        self._incoming.put_nowait(None)

        # Set `self._worker_task` to `None` so that when we'll be
        # waiting for the worker task to terminate, `self.is_running()`
        # will return `False` to prevent adding more events.
        worker = self._worker_task
        self._worker_task = None
        assert worker
        await worker
        self._logger.debug("Monitor stopped")

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
            exc = self._worker_task.exception()
            if exc:
                raise exc
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
            f"#{len(self._events)} ({self._events[-1]})"
            if not events_ended
            else "EndOfEvents"
        )

        for a, level in list(self.assertions.items()):

            if a.done:
                continue

            await a.update_events(events_ended=events_ended)

            if a.accepted:
                result = a.result()
                msg = "Assertion '%s' succeeded after event: %s; result: %s"
                self._logger.log(level, msg, a.name, event_descr, result)

            elif a.failed:
                await self._report_failure(a, event_descr)

    async def _report_failure(self, a: Assertion, event_descr: str) -> None:
        try:
            a.result()
        except Exception as exc:
            _exc_type, _exc, tb = sys.exc_info()
            # Drop top 3 frames from the traceback: the current one,
            # the one for `a.result()` and the one for the `func_wrapper`
            # used in `__init__()`, so that only the frames of the assertion
            # functions are left.
            for _ in (1, 2, 3):
                tb = tb.tb_next if tb else tb
            msg = "Assertion '%s' failed after event: %s; cause: %s"
            self._logger.error(
                msg, a.name, event_descr, exc, exc_info=(type(exc), exc, tb)
            )

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

    async def wait_for_event(
        self, predicate: Callable[[E], bool], timeout: Optional[float] = None
    ) -> E:
        """Wait for an event that satisfies given `predicate`.

        The first call to this method will examine all events gathered since
        this monitor was started and then, if needed, will wait for up to `timeout`
        seconds for a matching event.

        Subsequent calls will examine all events gathered since the previous call
        returned and then wait for up to `timeout` seconds.

        When `timeout` elapses, `asyncio.TimeourError` will be raised.
        """

        # First examine log lines already seen
        while self._last_checked_event + 1 < len(self._events):
            self._last_checked_event += 1
            event = self._events[self._last_checked_event]
            if predicate(event):
                return event

        # Otherwise create an assertion that waits for a matching event...
        async def wait_for_match(stream) -> E:
            async for e in stream:
                self._last_checked_event = len(stream.past_events) - 1
                if predicate(e):
                    return e
            raise AssertionError("No matching event occurred")

        assertion = self.add_assertion(wait_for_match, logging.DEBUG)

        # ... and wait until the assertion completes
        return await assertion.wait_for_result(timeout=timeout)
