"""Operators for building temporal assertions."""

import asyncio
from typing import Callable, Optional, TypeVar, TYPE_CHECKING

from goth.assertions import EventStream


if TYPE_CHECKING:

    from typing_extensions import Protocol

    class HasTimestamp(Protocol):
        """A protocol for objects with `timestamp` property."""

        @property
        def timestamp(self) -> float:
            """Return time at which this event occurred."""

    E = TypeVar("E", bound=HasTimestamp)

else:

    E = TypeVar("E")


EventPredicate = Callable[[E], bool]


async def eventually(
    stream: EventStream[E], predicate: EventPredicate, timeout: Optional[float] = None
) -> Optional[E]:
    """Wait for an event that satisfies `predicate` with `timeout`.

    Returns the first event satisfying `predicate` if any such event occurs
    before `timeout`, `None` if the end of events occurs before `timeout` and
    raises `asyncio.TimeoutError` otherwise.
    """
    # This operator could be generalised by:
    # 1) accepting an optional second predicate that would have to be true for each
    #    event *until* `predicate` holds;
    # 2) adding a flag that causes the whole `eventually()` assertion to fail
    #    if the end of events occurs before timeout.

    async def _coro():
        async for e in stream:
            if predicate(e):
                return e
        return None

    return await asyncio.wait_for(_coro(), timeout)
