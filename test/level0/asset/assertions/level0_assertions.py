"""Assertions related to API calls in Level 0 test scenario"""
from typing import Optional, Sequence

from src.api_monitor.api_events import APIEvent, APIRequest
import src.api_monitor.api_events as api

from src.assertions import AssertionFunction, TemporalAssertionError, logger
from src.assertions.operators import eventually

from .common_assertions import (
    APIEvents,
    assert_no_api_errors,
    assert_clock_ticks,
    assert_every_request_gets_response,
)


async def assert_first_request_is_import_key(stream: APIEvents) -> bool:
    """Assert that the first API request is for the `importKey` opertation."""

    async for e in stream:

        if isinstance(e, APIRequest):
            if api.is_import_key_request(e):
                return True
            raise TemporalAssertionError(str(e))

    return False


async def assert_eventually_subscribe_offer_called(stream: APIEvents) -> bool:
    """Assert that eventually `subscribeOffer` is called."""

    async for e in stream:

        if api.is_subscribe_offer_request(e):
            return True

    raise TemporalAssertionError("subscribeOffer not called")


# This is formally an assertion but it never fails:
async def wait_for_subscribe_offer_returned(stream: APIEvents) -> Optional[APIEvent]:
    """Wait for a response to a `subscribeOffer` request. Return the response event
    or `None` if the events end without the response.
    """

    async for e in stream:

        if api.is_subscribe_offer_response(e):
            assert isinstance(e, APIEvent)
            return e

    return None


async def assert_provider_periodically_collects_demands(stream: APIEvents) -> bool:
    """Assertion describing call patterns for the provider agent."""

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
            stream, lambda e: api.is_collect_demands_request(e, sub_id), deadline
        )
        if e:
            logger.debug("`collectDemands` called")
            deadline = e.timestamp + interval

    return True


TEMPORAL_ASSERTIONS: Sequence[AssertionFunction] = [
    assert_clock_ticks,
    assert_no_api_errors,
    assert_every_request_gets_response,
    assert_first_request_is_import_key,
    assert_provider_periodically_collects_demands,
]
