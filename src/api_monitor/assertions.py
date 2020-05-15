"""Coroutine-based implementation of temporal assertions"""

import asyncio
import logging
from typing import Any, AsyncIterable, Callable, Generic, Iterator, Sequence, TypeVar

from typing_extensions import Protocol


logger = logging.getLogger(__name__)


class TemporalAssertionError(AssertionError):
    """Thrown by temporal assertions on failure"""


E = TypeVar("E")


class EventSource(Protocol, AsyncIterable[E]):
    """A protocol used by assertion functions to observe a stream of events"""

    history: Sequence[E]
    """A sequence of past events, the last element is the most recent event"""


class Assertion(Generic[E]):
    """A class for executing assertion coroutines"""

    history: Sequence[E]
    """A sequence to which subsequent events are added"""

    name: str
    """Assertion name for logging etc."""

    _func: Callable[[Iterator[E]], Any]
    """A coroutine function that consumes the events and eventually
    returns this assertion's result
    """

    _task: asyncio.Task
    """A task in which the assertion coroutine runs"""

    _end_of_events: bool
    """A flag that signals the end of events"""

    _ready: asyncio.Event
    _processed: asyncio.Event
    """An event objects used for synchronising the client and the assertion coroutine"""

    def __init__(self, history: Sequence[E], func: Callable, *args: Any):
        self.history = history
        self.name = (
            f"{func.__module__}.{func.__name__}" f"({', '.join(str(a) for a in args)})"
        )
        self._task = asyncio.create_task(func(*args, self))
        self._end_of_events = False
        self._ready = asyncio.Event()
        self._processed = asyncio.Event()

    def __str__(self):
        status = "accepted" if self.accepted else "failed" if self.failed else "ongoing"
        return f"Assertion '{self.name}' ({status})"

    @property
    def done(self) -> bool:
        """Return `True` iff this assertion finished execution."""

        return self._task.done()

    @property
    def accepted(self) -> bool:
        """Return `True` iff this assertion finished execution successfuly."""

        return self._task.done() and self._task.exception() is None

    @property
    def failed(self) -> bool:
        """Return `True` iff this assertion finished execution by failing."""

        return self._task.done() and self._task.exception() is not None

    @property
    def result(self) -> Any:
        """Return either a value returned by this assertion on success, an exception
        thrown on failure, or `None` if the assertion haven't finished yet.
        """

        if self._task.done():
            if self._task.exception() is not None:
                return self._task.exception()
            return self._task.result()
        return None

    async def process_event(self):
        """Notify the assertion about a new event, wait until it's processed."""

        self._ready.set()
        await self._processed.wait()
        self._processed.clear()

    async def end_events(self):
        """Signal the end of events, wait for the assertion to react."""

        self._end_of_events = True
        await self.process_event()

    async def __aiter__(self):
        """Return a generator of events, to be used in assertion coroutines."""

        while True:

            await self._ready.wait()
            self._ready.clear()

            try:
                if self._end_of_events:
                    # this will end `async for ...` loop on this aync generator
                    return

                yield self.history[-1]

            finally:
                self._processed.set()
