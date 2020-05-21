import time

from src.assertions import EventStream
from src.assertions.monitor import EventMonitor


# Events are just integers
Events = EventStream[int]


async def assert_all_positive(stream: Events) -> None:

    async for e in stream:
        if e <= 0:
            raise AssertionError(f"{e} < 0")


async def assert_increasing(stream: Events) -> None:

    async for e in stream:
        # stream.past_events[-1] is `e`, stream.past_events[-2] is the previous event
        if len(stream.past_events) >= 2:
            prev = stream.past_events[-2]
            if prev >= e:
                raise AssertionError(f"{prev} >= {e}")


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


def test_monitor():

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

    # Feed events
    for n in [1, 3, 4, 5, 6, 7, 8, 9, 10]:
        monitor.add(n)
        time.sleep(0.3)

    monitor.stop()
