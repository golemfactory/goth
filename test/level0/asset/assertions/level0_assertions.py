"""Assertions related to API calls in Level 0 test scenario."""
import asyncio
import logging
from typing import Sequence

from goth.api_monitor.api_events import APIResponse
import goth.api_monitor.api_events as api

from goth.assertions import AssertionFunction, TemporalAssertionError
from goth.assertions.operators import eventually

from .common_assertions import (
    APIEvents,
    assert_no_api_errors,
)


logger = logging.getLogger("proxy")


async def assert_eventually_offer_subscribed(stream: APIEvents) -> APIResponse:
    """Assert that eventually `SubscribeOffer` is called and gets a response.

    Return the response event for the `SubscribeOffer` call, or `None` if
    the end of events occurs before the request is made or before the response
    arrives.
    """
    req = await eventually(stream, api.is_subscribe_offer_request)
    if req is None:
        # We've reached the End of Events
        raise TemporalAssertionError("SubscribeOffer not called")

    # Now wait for a response event matching `req`.
    resp = await eventually(
        stream, lambda e: isinstance(e, APIResponse) and e.request == req
    )
    if resp is None:
        raise TemporalAssertionError("no response to SubscribeOffer")

    return resp


async def assert_provider_periodically_collects_demands(stream: APIEvents) -> bool:
    """Assert call patterns for the provider agent."""

    # Make sure `SubscribeOffer` call is made; extract the subscription ID
    # from the response.
    response = await assert_eventually_offer_subscribed(stream)
    sub_id = api.get_response_json(response)
    logger.debug("SubscribeOffer returned sub_id %s", sub_id)

    interval = 10.0

    # Ensure that `CollectDemands(sub_id)` is called within each `interval`
    while not stream.events_ended:

        try:
            req = await eventually(
                stream, lambda e: api.is_collect_demands_request(e, sub_id), interval
            )
        except asyncio.TimeoutError:
            raise TemporalAssertionError(
                f"CollectDemands not called within the last {interval}s"
            )

        if req:
            logger.debug("CollectDemands called: %s", req)

    return True


async def assert_no_errors_until_invoice_sent(stream: APIEvents) -> None:
    """Assert there are no errors before the invoice is sent."""

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
    assert_provider_periodically_collects_demands,
    assert_no_errors_until_invoice_sent,
]
