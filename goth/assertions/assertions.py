"""Coroutine-based implementation of temporal assertions."""

import asyncio

from typing import (
    Any,
    AsyncIterator,
    AsyncIterable,
    Callable,
    Coroutine,
    Optional,
    Sequence,
    TypeVar,
    TYPE_CHECKING,
)


class TemporalAssertionError(AssertionError):
    """Thrown by temporal assertions on failure."""


E = TypeVar("E")
"""Type variable for the type of events"""


if TYPE_CHECKING:

    from typing_extensions import Protocol

    class EventStream(Protocol, AsyncIterable[E]):
        """A protocol for streams of events of type `E` used by assertion functions."""

        past_events: Sequence[E]
        """A sequence of past events, the last element is the most recent event."""

        events_ended: bool
        """`True` iff there will be no more events."""


else:

    EventStream = AsyncIterable


AssertionFunction = Callable[[EventStream[E]], Coroutine]


class Assertion(AsyncIterable[E]):
    """A class for executing assertion coroutines.

    An instance of this class wraps a coroutine function (called the
    "assertion coroutine") and provides an asynchronous generator of
    events that the assertion coroutine processes.
    After creating an instance of this class, its client should await
    the `update_events()` method each time a new event is appended to the list
    of events (the list is passed as an argument to `Assertion()`).
    After `update_events()` returns, the state of the assertion is updated
    and the client can query that state using the `done`, `accepted`
    and `failed` properties.
    """

    past_events: Sequence[E]
    """See `EventStream`."""

    events_ended: bool
    """See `EventStream`."""

    name: str
    """Assertion name for logging etc."""

    _func: Optional[AssertionFunction]
    """A coroutine function that is executed for this assertion."""

    _task: Optional[asyncio.Task]
    """A task in which the assertion coroutine runs."""

    _ready: Optional[asyncio.Event]
    """An event object used for synchronising the client and the assertion coroutine."""

    _processed: Optional[asyncio.Event]
    """An event object used for synchronising the client and the assertion coroutine."""

    _generator: Optional[AsyncIterator[E]]
    """An asynchronous generator that provides events to the assertion coroutine."""

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
        self._generator = None

    def start(self) -> asyncio.Task:
        """Create asyncio task that runs this assertion."""

        if self.started:
            raise RuntimeError("Assertion already started")

        def on_done(*args) -> None:
            """Notify the tasks waiting until this assertion updates."""
            self._notify_update_events()

        assert self._func is not None
        self._task = asyncio.create_task(self._func(self))
        self._task.add_done_callback(on_done)
        self._ready = asyncio.Event()
        self._processed = asyncio.Event()
        return self._task

    def __str__(self) -> str:
        status = "accepted" if self.accepted else "failed" if self.failed else "ongoing"
        return f"Assertion '{self.name}' ({status})"

    @property
    def started(self) -> bool:
        """Return `True` iff this assertion has started."""
        return self._task is not None

    @property
    def done(self) -> bool:
        """Return `True` iff this assertion finished execution."""
        return self.accepted or self.failed

    @property
    def accepted(self) -> bool:
        """Return `True` iff this assertion finished execution successfuly."""
        return self.started and self._task.done() and self._task.exception() is None

    @property
    def failed(self) -> bool:
        """Return `True` iff this assertion finished execution by failing."""
        return self.started and self._task.done() and self._task.exception() is not None

    async def result(self) -> Any:
        """Return the result of this assertion.

        If the assertion succeeded its result will be returned.
        If it failed, the exception will be raised.
        If the assertion hasn't finished yet, `None` will be returned.
        If it hasn't been started, `asyncio.InvalidStateError` will be raised.
        """
        if not self.started:
            raise asyncio.InvalidStateError("Assertion not started")

        if self._task.done():
            return await self._task
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

        # This will allow the assertion coroutine to resume execution
        self._ready.set()
        # Here we wait until the assertion coroutine yields control
        await self._processed.wait()
        self._processed.clear()

    def __aiter__(self) -> AsyncIterator[E]:
        """Return an asynchronous generator of events.

        It will yield events to `async for` loops in assertion coroutines.

        For a given assertion `A`, `A.__iter__()` is guaranteed to return
        the same asynchronous generator every time it's called.
        """
        if self._ready is None or self._processed is None:
            raise asyncio.InvalidStateError("Assertion not started")

        if self._generator is None:
            self._generator = self._create_generator()
        return self._generator

    def _notify_update_events(self) -> None:
        """Notify tasks waiting in `update_events()` that the update is processed."""
        self._ready.clear()
        self._processed.set()

    async def _create_generator(self) -> AsyncIterator[E]:
        """Create an asynchronous generator that will be returned by `__aiter__()`."""
        assert self._ready  # to silence mypy

        while True:
            # Wait for `update_events()` to signal that new event is available
            # or that the events ended.
            await self._ready.wait()
            if self.events_ended:
                return

            assert self.past_events
            yield self.past_events[-1]

            # It's important to notify the task waiting in `update_events()`
            # only after the control returns to this generator. In particular,
            # doing this in a `finally` clause wouldn't be correct, as the task
            # waiting in `update_events()` could be notified of processing an event
            # before the assertion coroutine could for example finish execution
            # and mark the assertion as finished.
            #
            # In case the control does not return (since the events end or
            # the assertion coroutine raises an exception), `_notify_update_events()`
            # is called in the done callback for the coroutine task.
            self._notify_update_events()
