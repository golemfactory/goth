"""Module with properties to be checked for the Level 0 test scenario"""
import logging
from typing import Sequence

from tracer_addon import CallTrace, APICall, trace_property


logger = logging.getLogger(__name__)


# A property is a function that takes a sequence of API calls and returns
# `bool`, decorated with `@trace_property` decorator


@trace_property
def delete_activity(calls: Sequence[APICall]) -> bool:
    """
    Check that each DeleteActivity(activityId) operation is preceded by
    CreateActivity(...) operation that returns this activiyId
    """

    # This is all too verbose, we should add some utility functions

    if not calls or not calls[-1].in_progress:
        return True

    last_call = calls[-1]
    if last_call.request.method != "DELETE":
        return True

    path = last_call.request.path
    if not path.startswith("/activity-api/v1/activity/"):
        return True

    activity_id = path.rsplit("/", 1)[-1]

    # Properties may also log messages (could be useful for debugging)
    logger.debug("Checking 'delete_actitity' property for activity %s", activity_id)

    # Look for ActivityCreate calls returning `activity_id`
    activity_create_calls = (
        call
        for call in reversed(calls[:-1])
        if (
            call.response
            and call.caller == last_call.caller
            and call.callee == last_call.callee
            and call.request.method == "POST"
            and call.request.path == "/activity-api/v1/activity"
            and call.response.text == f'"{activity_id}"'
        )
    )
    return any(activity_create_calls)
