"""Operators for building temporal assertions"""

from typing import Callable, Optional, TypeVar
from typing_extensions import Protocol

from src.assertions import EventStream, TemporalAssertionError


class HasTimestamp(Protocol):
    """A protocol for objects with `timestamp` property"""

    @property
    def timestamp(self) -> float:
        """Return time at which this event occurred"""


E = TypeVar("E", bound=HasTimestamp)

EventPredicate = Callable[[E], bool]


async def eventually(
    events: EventStream[E], predicate: EventPredicate, deadline: Optional[float] = None,
) -> Optional[E]:
    """Ensure `predicate` is satisfied for some event occurring before `deadline`."""

    async for e in events:

        if deadline is not None and e.timestamp > deadline:
            raise TemporalAssertionError(
                f"Timeout: {e.timestamp - deadline}s after deadline"
            )

        if predicate(e):
            return e

    return None
