"""Test the `assertions.monitor`."""

import asyncio

import pytest

from goth.assertions import EventStream
from goth.assertions.monitor import EventMonitor


# Events are just integers
Events = EventStream[int]


async def assert_all_positive(stream: Events) -> None:
    """Assert all events are positive."""

    async for e in stream:
        assert e > 0


async def assert_increasing(stream: Events) -> None:
    """Assert all events increasing numbers."""

    async for e in stream:
        # stream.past_events[-1] is `e`, stream.past_events[-2] is the previous event
        if len(stream.past_events) >= 2:
            prev = stream.past_events[-2]
            assert prev < e


async def assert_eventually_five(stream: Events) -> None:
    """Assert the event will eventually be five."""

    async for e in stream:
        if e == 5:
            return  # success!

    raise AssertionError("Events ended")


async def assert_eventually_even(stream: Events) -> int:
    """Assert the event will eventually be even."""

    async for e in stream:
        if e % 2 == 0:
            return e

    raise AssertionError("Events ended")


async def assert_eventually_greater(n: int, stream: Events) -> int:
    """Assert the event will eventually be greater then `n`."""

    async for e in stream:
        if e > n:
            return e

    raise AssertionError("Events ended")


async def assert_fancy_property(stream: Events) -> int:
    """Assert the event to match multiple other assertions.

    - assert_eventually_even
    - assert_eventually_greater
    """

    n = await assert_eventually_even(stream)
    m = await assert_eventually_greater(n * 2, stream)
    assert m % 2 == 1
    return m


@pytest.mark.asyncio
async def test_assertions():
    """Test a dummy set of assertions against a list of int's."""

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
        await monitor.add_event(n)

    # Need this sleep to make sure the assertions consume the events
    await asyncio.sleep(0.1)

    failed = {a.name.rsplit(".", 1)[-1] for a in monitor.failed}
    assert failed == {"assert_increasing"}

    satisfied = {a.name.rsplit(".", 1)[-1] for a in monitor.satisfied}
    assert satisfied == {"assert_fancy_property"}

    # Certain assertions can only accept/fail after the monitor is stopped
    await monitor.stop()

    failed = {a.name.rsplit(".", 1)[-1] for a in monitor.failed}
    assert failed == {"assert_increasing", "assert_eventually_five"}

    satisfied = {a.name.rsplit(".", 1)[-1] for a in monitor.satisfied}
    assert satisfied == {"assert_all_positive", "assert_fancy_property"}


@pytest.mark.asyncio
async def test_not_started_raises_on_add_event():
    """Test whether `add_event()` invoked before starting the monitor raises error."""

    monitor = EventMonitor()

    with pytest.raises(RuntimeError):
        await monitor.add_event(1)


@pytest.mark.asyncio
async def test_stopped_raises_on_add_event():
    """Test whether `add_event()` invoked after stopping the monitor raises error."""

    monitor = EventMonitor()

    monitor.start()
    await monitor.stop()

    with pytest.raises(RuntimeError):
        await monitor.add_event(1)


@pytest.mark.asyncio
async def test_waitable_monitor():
    """Test if `WaitableMonitor.wait_for_event()` respects event ordering."""

    monitor = EventMonitor()
    monitor.start()

    events = []

    async def wait_for_events():
        events.append(await monitor.wait_for_event(lambda e: e == 1))
        events.append(await monitor.wait_for_event(lambda e: e == 2))
        events.append(await monitor.wait_for_event(lambda e: e == 3))

    await monitor.add_event(0)
    await monitor.add_event(1)
    await monitor.add_event(2)
    await monitor.add_event(0)

    task = asyncio.create_task(wait_for_events())
    await asyncio.sleep(0.1)
    assert events == [1, 2]

    await monitor.add_event(3)
    await asyncio.sleep(0.1)
    assert events == [1, 2, 3]

    assert task.done()
    await monitor.stop()


@pytest.mark.asyncio
async def test_waitable_monitor_timeout_error():
    """Test if `WaitableMonitor.wait_for_event()` raises `TimeoutError` on timeout."""

    monitor = EventMonitor()
    monitor.start()

    with pytest.raises(asyncio.TimeoutError):
        await monitor.wait_for_event(lambda e: e == 1, timeout=0.1)

    await monitor.stop()


@pytest.mark.asyncio
async def test_waitable_monitor_timeout_success():
    """Test if `WaitableMonitor.wait_for_event()` return success before timeout."""

    monitor = EventMonitor()
    monitor.start()

    async def worker_task():
        await asyncio.sleep(0.1)
        await monitor.add_event(1)

    asyncio.create_task(worker_task())

    await monitor.wait_for_event(lambda e: e == 1, timeout=1.0)
    await monitor.stop()
