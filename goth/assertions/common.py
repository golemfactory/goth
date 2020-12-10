"""Common assertions related to API calls."""
from typing import Set

from goth.api_monitor.api_events import (
    APIEvent,
    APIError,
    APIRequest,
    APIResponse,
)

from goth.assertions import EventStream


APIEvents = EventStream[APIEvent]


async def assert_no_api_errors(stream: APIEvents) -> bool:
    """Assert that no instance of `APIError` event ever occurs."""
    async for e in stream:

        if isinstance(e, APIError):
            raise AssertionError(f"API error occurred: {e}")

    return True


async def assert_every_request_gets_response(stream: APIEvents) -> bool:
    """Assert that every request gets a response.

    Assert that for every `APIRequest` event there will eventually occur a
    corresponding `APIResponse` event.
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
        raise AssertionError(f"request got no response: {a_request}")

    return True
