"""Coroutine-based implementation of temporal assertions"""

import asyncio

# import logging
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Coroutine,
    Optional,
    Sequence,
    TypeVar,
)

from typing_extensions import Protocol


class TemporalAssertionError(AssertionError):
    """Thrown by temporal assertions on failure"""


E = TypeVar("E")
"""Type variable for the type of events"""


class EventStream(Protocol, AsyncIterable[E]):
    """A protocol for streams of events of type `E` used by assertion functions"""

    past_events: Sequence[E]
    """A sequence of past events, the last element is the most recent event"""

    events_ended: bool
    """`True` iff there will be no more events"""


AssertionFunction = Callable[[EventStream[E]], Coroutine]


class Assertion(AsyncIterable[E]):
    """A class for executing assertion coroutines"""

    past_events: Sequence[E]
    """See `EventStream`"""

    events_ended: bool
    """See `EventStream`"""

    name: str
    """Assertion name for logging etc"""

    _func: Optional[AssertionFunction]
    """A coroutine function that is executed for this assertion"""

    _task: Optional[asyncio.Task]
    """A task in which the assertion coroutine runs"""

    _ready: Optional[asyncio.Event]
    """An event object used for synchronising the client and the assertion coroutine"""

    _processed: Optional[asyncio.Event]
    """An event object used for synchronising the client and the assertion coroutine"""

    def __init__(self, events: Sequence[E], func: AssertionFunction) -> None:
        self.past_events = events
        self.events_ended = False
        self.name = f"{func.__module__}.{func.__name__}"
        self._func = func
        # Creating asyncio objects is decoupled from object initialisation to
        # allow this object to be created and run in different threads (and thus
        # in different event loops).
        self._task = None
        self._ready = None
        self._processed = None

    def start(self) -> asyncio.Task:
        """Create asyncio task that runs this assertion."""

        assert self._func is not None
        self._task = asyncio.create_task(self._func(self))
        self._ready = asyncio.Event()
        self._processed = asyncio.Event()
        return self._task

    def __str__(self) -> str:
        status = "accepted" if self.accepted else "failed" if self.failed else "ongoing"
        return f"Assertion '{self.name}' ({status})"

    @property
    def done(self) -> bool:
        """Return `True` iff this assertion finished execution."""

        return self.accepted or self.failed

    @property
    def accepted(self) -> bool:
        """Return `True` iff this assertion finished execution successfuly."""

        return (
            self._task is not None
            and self._task.done()
            and self._task.exception() is None
        )

    @property
    def failed(self) -> bool:
        """Return `True` iff this assertion finished execution by failing."""

        return (
            self._task is not None
            and self._task.done()
            and self._task.exception() is not None
        )

    @property
    def result(self) -> Any:
        """
        Return either a value returned by this assertion on success, an exception
        thrown on failure, or `None` if the assertion haven't finished yet.
        """

        if self._task is None:
            raise asyncio.InvalidStateError("Assertion not started")

        if self._task.done():
            if self._task.exception() is not None:
                return self._task.exception()
            return self._task.result()
        return None

    async def update_events(self, events_ended: bool = False) -> None:
        """Notify the assertion that a new event has been added."""

        if self.events_ended:
            raise AssertionError("Event stream already ended")
        self.events_ended = events_ended

        if self._ready is None or self._processed is None:
            raise asyncio.InvalidStateError("Assertion not started")

        if self.done:
            return

        # This will allow the assertion function to resume execution
        self._ready.set()
        # Here we wait until the assertion function yields control
        await self._processed.wait()
        self._processed.clear()

    async def __aiter__(self) -> AsyncIterator[E]:
        """Return a generator of events, to be used in assertion coroutines."""

        if self._ready is None or self._processed is None:
            raise asyncio.InvalidStateError("Assertion not started")

        while True:

            await self._ready.wait()
            self._ready.clear()

            try:
                if self.events_ended:
                    # this will end `async for ...` loop on this aync generator
                    return

                assert self.past_events
                yield self.past_events[-1]

            finally:
                self._processed.set()
