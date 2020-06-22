# Assertions by example

Below are example assertions that express properties of streams of events.
For now, events are just integers, that is, values of type `int`.

Let's start with the required imports:
```
from goth.assertions import EventStream
from goth.assertions.monitor import EventMonitor
```

Streams of events are values of type `EventStream[int]`. This type extends
the `AsyncIterable[int]` protocol, which means that one can iterate over
a stream of events using an `async for` loop.

An assertion is just a Python coroutine (a function defined with `async def`) that takes a value of type `EventStream[int]` as the only argument.

The following assertion checks that all events (integers) are positive.

```
async def assert_all_positive(stream: EventStream[int]):

    async for n in stream:
        assert n <= 0
    
    # If we'here it means that there will be no more events
    return

```

The assertion **fails** by raising an exception. If the assertion returns normally, this indicates that the assertion **succeeded**. In both cases, the assertion does not need to see any more events. 

Note: normal return from an assertion function always means that the assertion succeeded, even if the returned value is `False` or `None`.

Another example is an assertion that checks that an even number will eventually
occur in the event stream:

```
aync def assert_eventually_even(stream: EventStream[int]) -> int:

    async for n in stream:
        if n % 2 == 0:
            return n

    assert False, "Expected an even number"
```

Since assertions are Python coroutines, they can be easily combined into more complex assertions:

```
async def assert_fancy(stream: EventStream[int]):

    # Assert that an even number to occurs
    n = await assert_eventually_even(stream)
    
    # Assert that another even number occurs
    m = await assert_eventually_even(stream)

    # Assert that the second even number is twice the first one
    assert m == 2 * n
```

## Running assertions

Assertions can be run in an `EventMonitor`:
```
monitor: EventMonitor[int] = EventMonitor()
monitor.add_assertions([
    assert_all_positive,
    assert_eventually_even,
    assert_fancy
])

monitor.start()

# Now feed some events to the monitor
for n in [1, 3, 4, 6, -7, 8, 9, 10]:
    monitor.add_event(n)

# This will notify the assertions that the events ended
monitor.stop()

# Print the assertions that succeeded:
for a in monitor.succeeded:
    print(f"Succeded: {a.name}")

# And the ones that failed:
for a in monitor.failed:
    print(f"Failed: {a.name}")
```
