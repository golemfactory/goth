from typing import Callable, Optional, TypeVar, Union

from src.assertions import EventStream, HasTimestamp, TemporalAssertionError
from src.assertions.monitor import TimerEvent


E = TypeVar("E", bound=HasTimestamp)


async def eventually(
    events: EventStream[Union[E, TimerEvent]],
    predicate: Callable[[E], bool],
    deadline: Optional[float] = None,
) -> Optional[E]:
    """Ensure `predicate` is satisfied for some event occurring before `deadline`."""

    async for e in events:

        if deadline is not None and e.timestamp > deadline:
            raise TemporalAssertionError(
                f"Timeout: {e.timestamp - deadline}s after deadline"
            )

        if not isinstance(e, TimerEvent) and predicate(e):
            return e

    return None
