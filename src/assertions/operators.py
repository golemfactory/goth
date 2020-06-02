"""Operators for building temporal assertions"""

from typing import Callable, Optional, TypeVar, TYPE_CHECKING

from src.assertions import EventStream


if TYPE_CHECKING:

    from typing_extensions import Protocol

    class HasTimestamp(Protocol):
        """A protocol for objects with `timestamp` property"""

        @property
        def timestamp(self) -> float:
            """Return time at which this event occurred"""

    E = TypeVar("E", bound=HasTimestamp)

else:

    E = TypeVar("E")


EventPredicate = Callable[[E], bool]


async def eventually(
    events: EventStream[E], predicate: EventPredicate, deadline: Optional[float] = None
) -> Optional[E]:
    """Ensure `predicate` is satisfied for some event occurring before `deadline`."""

    async for e in events:

        assert (
            deadline is None or e.timestamp <= deadline
        ), f"Timeout: {(e.timestamp - deadline):.1f}s after deadline"

        if predicate(e):
            return e

    return None
