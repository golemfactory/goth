"""Common assertions related to API calls"""
from typing import Set

from goth.api_monitor.api_events import (
    APIEvent,
    APIClockTick,
    APIError,
    APIRequest,
    APIResponse,
)

from goth.assertions import EventStream, TemporalAssertionError


APIEvents = EventStream[APIEvent]


async def assert_no_api_errors(stream: APIEvents) -> bool:
    """Assert that no instance of `APIError` event ever occurs."""

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

        if isinstance(e, APIClockTick):
            last_timer_event = e.timestamp

    if last_timer_event is None:
        raise TemporalAssertionError("No timer events")

    return True


async def assert_every_request_gets_response(stream: APIEvents) -> bool:
    """Assert that for every `APIRequest` event there will eventually occur
    a corresponding `APIResponse` event.
    """

    requests_in_progress: Set[APIRequest] = set()

    async for e in stream:

        if isinstance(e, APIRequest):
            requests_in_progress.add(e)
        elif isinstance(e, APIResponse):
            assert e.request in requests_in_progress
            requests_in_progress.remove(e.request)

    if requests_in_progress:
        a_request = requests_in_progress.pop()
        raise TemporalAssertionError(f"request got no response: {a_request}")

    return True
