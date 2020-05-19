import time
from typing import Callable, Coroutine, Optional, Sequence, Set

from api_events import APICall, APIError, APIEvent, APIResult
import api_events as api

from assertions import logger, AssertionFunction, EventStream, TemporalAssertionError


APIEvents = EventStream[APIEvent]


async def assert_no_api_errors(stream: APIEvents) -> bool:

    async for e in stream:

        if isinstance(e, APIError):
            raise TemporalAssertionError("API error occurred")

    return True


async def assert_first_call_is_import_key(stream: APIEvents) -> bool:

    async for _ in stream:

        if stream.past_events and api.is_import_key_call(stream.past_events[0]):
            return True
        raise TemporalAssertionError("First API call is not importKey")

    return False


async def assert_eventually_subscribe_offer_called(stream: APIEvents) -> bool:

    async for e in stream:

        if isinstance(e, APIEvent) and api.is_subscribe_offer_call(e):
            return True

    raise TemporalAssertionError("subscribeOffer not called")


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


# This is formally an assertion but it never fails:
async def wait_for_subscribe_offer_returned(stream: APIEvents) -> str:
    """Wait for a response to a `subscribeOffer` call and return
    the subscription ID contained in the response.
    """

    async for e in stream:

        if isinstance(e, APIEvent) and api.is_subscribe_offer_response(e):
            return api.get_response_json(e)

    raise TemporalAssertionError("subscribeOffer did not return")


async def eventually(
    events: APIEvents,
    predicate: Callable[[APIEvent], bool],
    timeout: Optional[float] = None,
) -> Optional[APIEvent]:
    """Ensure `predicate` is satified for some event occurring before `timeout`."""

    start_time = time.time()

    async for e in events:

        if timeout is not None and time.time() > start_time + timeout:
            raise TemporalAssertionError("Timeout")

        if isinstance(e, APIEvent) and predicate(e):
            return e

    if time.time() > start_time + timeout:
        raise TemporalAssertionError("Timeout")

    return None


# A relatively complex assertion specifying the behaviour of the provider agent
async def assert_provider_periodically_collects_demands(stream: APIEvents) -> bool:

    await assert_eventually_subscribe_offer_called(stream)
    sub_id = await wait_for_subscribe_offer_returned(stream)
    logger.debug("`subscribeOffer` returned sub_id %s", sub_id)

    while not stream.events_ended:

        e = await eventually(
            stream, lambda e: api.is_collect_demands_call(e, sub_id), 4.0
        )
        if e:
            logger.debug("`collectDemands` called")

    return True


TEMPORAL_ASSERTIONS: Sequence[AssertionFunction] = [
    assert_no_api_errors,
    assert_every_call_gets_response,
    assert_first_call_is_import_key,
    assert_provider_periodically_collects_demands,
]
