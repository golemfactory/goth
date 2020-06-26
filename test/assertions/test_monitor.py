import asyncio
from unittest import mock

import pytest

from goth.assertions import EventStream
from goth.assertions.messages import (
    AssertionFailureMessage,
    AssertionStartMessage,
    AssertionSuccessMessage,
    parse_assertion_message,
)
from goth.assertions.monitor import EventMonitor


# Events are just integers
Events = EventStream[int]


async def assert_all_positive(stream: Events) -> None:

    async for e in stream:
        assert e > 0


async def assert_increasing(stream: Events) -> None:

    async for e in stream:
        # stream.past_events[-1] is `e`, stream.past_events[-2] is the previous event
        if len(stream.past_events) >= 2:
            prev = stream.past_events[-2]
            assert prev < e


async def assert_eventually_five(stream: Events) -> None:

    async for e in stream:
        if e == 5:
            return  # success!

    raise AssertionError("Events ended")


async def assert_eventually_even(stream: Events) -> int:

    async for e in stream:
        if e % 2 == 0:
            return e

    raise AssertionError("Events ended")


async def assert_eventually_greater(n: int, stream: Events) -> int:

    async for e in stream:
        if e > n:
            return e

    raise AssertionError("Events ended")


async def assert_fancy_property(stream: Events) -> int:

    n = await assert_eventually_even(stream)
    m = await assert_eventually_greater(n * 2, stream)
    assert m % 2 == 1
    return m


@pytest.mark.asyncio
async def test_assertions():

    monitor: EventMonitor[int] = EventMonitor()
    monitor.add_assertions(
        [
            assert_all_positive,
            assert_increasing,
            assert_eventually_five,
            assert_fancy_property,
        ]
    )
    monitor.start()

    for n in [1, 3, 4, 6, 3, 8, 9, 10]:
        monitor.add_event(n)

    await monitor.stop()

    failed = {a.name.rsplit(".", 1)[-1] for a in monitor.failed}
    assert failed == {"assert_increasing", "assert_eventually_five"}

    satisfied = {a.name.rsplit(".", 1)[-1] for a in monitor.satisfied}
    assert satisfied == {"assert_all_positive", "assert_fancy_property"}


@pytest.mark.asyncio
async def test_not_started_raises_on_add_event():
    """Test whether `add_event()` invoked before starting the monitor raises error."""

    monitor: EventMonitor[int] = EventMonitor()

    with pytest.raises(RuntimeError):
        monitor.add_event(1)


@pytest.mark.asyncio
async def test_stopped_raises_on_add_event():
    """Test whether `add_event()` invoked after stopping the monitor raises error."""

    monitor: EventMonitor[int] = EventMonitor()

    monitor.start()
    await monitor.stop()

    with pytest.raises(RuntimeError):
        monitor.add_event(1)


@pytest.mark.asyncio
async def test_monitor_messages():
    """Test if a monitor outputs correct assertion messages"""

    messages = []

    mock_file = mock.MagicMock()
    mock_file.write = messages.append

    def _check_message(msg, msg_class, func):
        assert isinstance(msg, msg_class)
        assert msg.assertion == f"{func.__module__}.{func.__name__}"

    monitor: EventMonitor[int] = EventMonitor(messages_file=mock_file)

    assertions = [
        assert_increasing,
        assert_all_positive,
        assert_eventually_five,
        assert_eventually_even,
    ]

    monitor.add_assertions(assertions)

    assert len(messages) == 4
    parsed = [parse_assertion_message(msg) for msg in messages]
    expected = [
        AssertionStartMessage(f"{func.__module__}.{func.__name__}")
        for func in assertions
    ]
    assert parsed == expected

    monitor.start()

    for n in [1, 3, 4, 6, 3, 8]:
        monitor.add_event(n)
        # Need this sleep to make sure the assertions consume the events
        await asyncio.sleep(0.2)

    assert len(messages) == 6
    parsed = [parse_assertion_message(msg) for msg in messages[4:]]
    assert len(parsed) == 2
    _check_message(parsed[0], AssertionSuccessMessage, assert_eventually_even)
    assert parsed[0].result == "4"
    _check_message(parsed[1], AssertionFailureMessage, assert_increasing)

    await monitor.stop()

    assert len(messages) == 8
    parsed = [parse_assertion_message(msg) for msg in messages[6:]]
    assert len(parsed) == 2
    _check_message(parsed[0], AssertionSuccessMessage, assert_all_positive)
    _check_message(parsed[1], AssertionFailureMessage, assert_eventually_five)
