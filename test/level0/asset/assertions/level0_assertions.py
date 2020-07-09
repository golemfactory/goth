"""Assertions related to API calls in Level 0 test scenario"""
import logging
from typing import Optional, Sequence

from goth.api_monitor.api_events import APIEvent
import goth.api_monitor.api_events as api

from goth.assertions import AssertionFunction, TemporalAssertionError
from goth.assertions.operators import eventually

from .common_assertions import (
    APIEvents,
    assert_no_api_errors,
    assert_clock_ticks,
)


logger = logging.getLogger(__name__)


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

    interval = 6.0
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


async def assert_no_errors_until_invoice_sent(stream: APIEvents) -> None:

    try:
        await assert_no_api_errors(stream)

    except TemporalAssertionError as err:
        # After the invoice is sent the test is finished and the containers are
        # shut down, and hence some API requests may get no response
        if any(api.is_invoice_send_response(e) for e in stream.past_events):
            logger.warning("API error occurred after invoice send response, ignoring")
        else:
            logger.warning("API error occurred before invoice send response")
            raise err


TEMPORAL_ASSERTIONS: Sequence[AssertionFunction] = [
    assert_clock_ticks,
    assert_provider_periodically_collects_demands,
    assert_no_errors_until_invoice_sent,
]
