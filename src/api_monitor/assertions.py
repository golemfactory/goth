"""Coroutine-based implementation of temporal assertions"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Coroutine,
    Sequence,
    TypeVar,
    Union,
)

from typing_extensions import Protocol


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG
)

logger = logging.getLogger(__name__)
_file_handler = logging.FileHandler("assert.log", mode="w")
_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
logger.handlers = [_file_handler]


class TemporalAssertionError(AssertionError):
    """Thrown by temporal assertions on failure"""


@dataclass(frozen=True)
class HeartbeatEvent:
    """Represents occurrences of hartbeat events"""

    time: float


E = TypeVar("E")


class EventStream(Protocol, AsyncIterable[Union[E, HeartbeatEvent]]):
    """A protocol used by assertion functions to observe a stream of events"""

    past_events: Sequence[E]
    """A sequence of past events, the last element is the most recent event"""

    events_ended: bool
    """`True` iff there will be no more events"""


AssertionFunction = Callable[[EventStream], Coroutine]


class Assertion(AsyncIterable[Union[E, HeartbeatEvent]]):
    """A class for executing assertion coroutines"""

    past_events: Sequence[E]
    """A sequence to which subsequent events are added"""

    events_ended: bool
    """A flag that signals that there will be no more events"""

    name: str
    """Assertion name for logging etc."""

    _task: asyncio.Task
    """A task in which the assertion coroutine runs"""

    _last_event_is_harbeat: bool
    """True iff the last event is a hartbeat event"""

    _ready: asyncio.Event

    _processed: asyncio.Event
    """An event objects used for synchronising the client and the assertion coroutine"""

    def __init__(self, events: Sequence[E], func: AssertionFunction) -> None:
        self.past_events = events
        self.events_ended = False
        self.name = f"{func.__module__}.{func.__name__}"
        self._task = asyncio.create_task(func(self))
        self._last_event_is_hartbeat = False
        self._ready = asyncio.Event()
        self._processed = asyncio.Event()

    def __str__(self) -> str:
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

    async def process_event(self, is_hartbeat: bool = False) -> None:
        """Notify the assertion about a new event, wait until it's processed."""

        self._last_event_is_harbeat = is_hartbeat
        self._ready.set()
        await self._processed.wait()
        self._processed.clear()

    async def end_events(self) -> None:
        """Signal the end of events, wait for the assertion to react."""

        self.events_ended = True
        await self.process_event()

    async def __aiter__(self) -> AsyncIterator[Union[E, HeartbeatEvent]]:
        """Return a generator of events, to be used in assertion coroutines."""

        while True:

            await self._ready.wait()
            self._ready.clear()

            try:
                if self.events_ended:
                    # this will end `async for ...` loop on this aync generator
                    return

                if not self._last_event_is_harbeat:
                    yield self.past_events[-1]
                else:
                    yield HeartbeatEvent(time.time())

            finally:
                self._processed.set()
