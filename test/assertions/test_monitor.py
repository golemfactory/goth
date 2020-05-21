from dataclasses import dataclass
import time

from src.assertions import EventStream
from src.assertions.monitor import EventMonitor


@dataclass(frozen=True)
class NumEvent:
    data: int


Events = EventStream[NumEvent]


async def assert_all_positive(stream: Events) -> None:

    async for e in stream:
        if e.data <= 0:
            raise AssertionError(f"{e.data} < 0")


async def assert_increasing(stream: Events) -> None:

    async for _ in stream:
        # stream.past_events[-1] is the most recent `NumEvent`
        if len(stream.past_events) >= 2:
            current_number = stream.past_events[-1].data
            previous_number = stream.past_events[-2].data
            if previous_number >= current_number:
                raise AssertionError(f"{previous_number} >= {current_number}")


async def assert_eventually_five(stream: Events) -> None:

    async for e in stream:
        if e.data == 5:
            return  # success!

    raise AssertionError("Events ended")


async def assert_eventually_even(stream: Events) -> int:

    async for e in stream:
        if e.data % 2 == 0:
            return e.data

    raise AssertionError("Events ended")


async def assert_eventually_greater(n: int, stream: Events) -> int:

    async for e in stream:
        if e.data > n:
            return e.data

    raise AssertionError("Events ended")


async def assert_fancy_property(stream: Events) -> int:

    n = await assert_eventually_even(stream)
    m = await assert_eventually_greater(n * 2, stream)
    assert m % 2 == 1
    return m


def test_monitor():

    monitor: EventMonitor[NumEvent] = EventMonitor()
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
        monitor.add(NumEvent(n))
        time.sleep(0.3)

    monitor.stop()
