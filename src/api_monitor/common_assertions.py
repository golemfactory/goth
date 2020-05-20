"""Common assertions related to API calls"""
from typing import Callable, Optional, Set, Union

from src.api_monitor.api_events import APIEvent, APICall, APIError, APIResult

from src.assertions import EventStream, TemporalAssertionError, logger
from src.assertions.monitor import TimerEvent

APIEvents = EventStream[Union[APIEvent, TimerEvent]]


async def assert_no_api_errors(stream: APIEvents) -> bool:

    async for e in stream:

        if isinstance(e, APIError):
            raise TemporalAssertionError("API error occurred")

    return True


async def assert_clock_ticks(stream: APIEvents) -> bool:
    """Assert at least one timer event occurred and the distance between
    any event the last timer event is less than 1.5s"""

    last_timer_event = None

    async for e in stream:

        if last_timer_event is not None and e.timestamp > last_timer_event + 1.5:
            raise TemporalAssertionError()

        if isinstance(e, TimerEvent):
            last_timer_event = e.timestamp

    if last_timer_event is None:
        raise TemporalAssertionError("No timer events")

    return True


async def assert_every_call_gets_response(stream: APIEvents) -> bool:

    calls_in_progress: Set[APICall] = set()

    async for e in stream:

        if isinstance(e, APICall):
            calls_in_progress.add(e)
        elif isinstance(e, APIResult):
            assert e.call in calls_in_progress
            calls_in_progress.remove(e.call)

    if calls_in_progress:
        a_call = calls_in_progress.pop()
        raise TemporalAssertionError(f"call got no response: {a_call}")

    return True
