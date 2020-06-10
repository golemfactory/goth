import pytest

from assertions import EventStream
from assertions.monitor import EventMonitor


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

    assert False, "Events ended"


async def assert_eventually_even(stream: Events) -> int:

    async for e in stream:
        if e % 2 == 0:
            return e

    assert False, "Events ended"


async def assert_eventually_greater(n: int, stream: Events) -> int:

    async for e in stream:
        if e > n:
            return e

    assert False, "Events ended"


async def assert_fancy_property(stream: Events) -> int:

    n = await assert_eventually_even(stream)
    m = await assert_eventually_greater(n * 2, stream)
    assert m % 2 == 1
    return m


def test_assertions():

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

    monitor.stop()

    failed = {a.name.rsplit(".", 1)[-1] for a in monitor.failed}
    assert failed == {"assert_increasing", "assert_eventually_five"}

    satisfied = {a.name.rsplit(".", 1)[-1] for a in monitor.satisfied}
    assert satisfied == {"assert_all_positive", "assert_fancy_property"}


def test_not_started_raises_on_add_event():
    """Test whether `add_event()` invoked before starting the monitor raises error."""

    monitor: EventMonitor[int] = EventMonitor()

    with pytest.raises(RuntimeError):
        monitor.add_event(1)


def test_stopped_raises_on_add_event():
    """Test whether `add_event()` invoked after stopping the monitor raises error."""

    monitor: EventMonitor[int] = EventMonitor()

    monitor.start()
    monitor.stop()

    with pytest.raises(RuntimeError):
        monitor.add_event(1)
