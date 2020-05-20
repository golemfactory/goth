from typing import Callable, Optional, Sequence, Set, Tuple

from api_events import APICall, APIError, APIEvent, APIResult
import api_events as api

from assertions import logger, AssertionFunction, EventStream, TemporalAssertionError
from api_monitor import APIorTimerEvent, TimerEvent


APIEvents = EventStream[APIorTimerEvent]


async def assert_no_api_errors(stream: APIEvents) -> bool:

    async for e in stream:

        if isinstance(e, APIError):
            raise TemporalAssertionError("API error occurred")

    return True


async def assert_first_call_is_import_key(stream: APIEvents) -> bool:

    async for _ in stream:

        if stream.past_events:
            if api.is_import_key_call(stream.past_events[0]):
                return True
            raise TemporalAssertionError(str(stream.past_events[0]))

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
async def wait_for_subscribe_offer_returned(stream: APIEvents) -> Optional[APIEvent]:
    """Wait for a response to a `subscribeOffer` call. Return the response event
    or `None` if the events end without the response.
    """

    async for e in stream:

        if api.is_subscribe_offer_response(e):
            return e

    return None


async def eventually(
    events: APIEvents,
    predicate: Callable[[APIEvent], bool],
    deadline: Optional[float] = None,
) -> Optional[APIEvent]:
    """Ensure `predicate` is satisfied for some event occurring before `deadline`."""

    async for e in events:

        if deadline is not None and e.timestamp > deadline:
            raise TemporalAssertionError(f"Timeout: time = {e.timestamp} > {deadline}")

        if isinstance(e, APIEvent) and predicate(e):
            return e

    return None


# A relatively complex assertion specifying the behaviour of the provider agent
async def assert_provider_periodically_collects_demands(stream: APIEvents) -> bool:

    # 1. Make sure subscribeOffer is called
    await assert_eventually_subscribe_offer_called(stream)

    # 2. After subscribeOffer is responded, extract subscription ID from response
    #    (this step does not fail if the response never comes!)
    response = await wait_for_subscribe_offer_returned(stream)
    if response is None:
        # This means the response did not arrive and the events ended
        return True

    sub_id = api.get_response_json(response)
    logger.debug("`subscribeOffer` returned sub_id %s", sub_id)

    interval = 5.0
    deadline = response.timestamp + interval

    # 3. Ensure that `collectDemands` is called within each `interval`
    while not stream.events_ended:

        e = await eventually(
            stream, lambda e: api.is_collect_demands_call(e, sub_id), deadline
        )
        if e:
            logger.debug("`collectDemands` called")
            deadline = e.timestamp + interval

    return True


async def assert_clock_ticks(stream: APIEvents) -> bool:
    """Assert at least one timer event occurred and the distance between
    any event the last timer event is less than 1.5s"""

    last_timer_event = None

    async for e in stream:

        if last_timer_event is not None and e.timestamp > last_timer_event + 1.5:
            raise TemporalAssertionError()

        if isinstance(e, TimerEvent):
            logger.debug("tick.")
            last_timer_event = e.timestamp

    if last_timer_event is None:
        raise TemporalAssertionError("No timer events")



TEMPORAL_ASSERTIONS: Sequence[AssertionFunction] = [
    assert_clock_ticks,
    assert_no_api_errors,
    assert_every_call_gets_response,
    assert_first_call_is_import_key,
    assert_provider_periodically_collects_demands,
]
