"""Unit tests for `assertions.assertions` module."""

import asyncio
import pytest

from goth.assertions import Assertion


@pytest.mark.asyncio
async def test_assertion_not_started_raises():
    """Test if an assertion raises when it is used before starting."""

    events = []

    async def func(_stream):
        return

    assertion = Assertion(events, func)
    assert not assertion.done
    assert not assertion.accepted
    assert not assertion.failed
    with pytest.raises(asyncio.InvalidStateError):
        _ = assertion.result
    with pytest.raises(asyncio.InvalidStateError):
        await assertion.update_events()


@pytest.mark.asyncio
async def test_assertion_accept_immediately():
    """Test if an assertion passes when it accepts immediately."""

    events = []

    async def func(_stream):
        return 43

    assertion = Assertion(events, func)
    task = assertion.start()
    await task
    assert assertion.done
    assert assertion.accepted
    assert assertion.result == 43


@pytest.mark.asyncio
async def test_assertion_accept_with_delay():
    """Test if an assertion passes when it accepts after a delay."""

    events = []

    async def func(_stream):
        await asyncio.sleep(0.2)
        return 43

    assertion = Assertion(events, func)
    task = assertion.start()
    await task
    assert assertion.done
    assert assertion.accepted
    assert assertion.result == 43


@pytest.mark.asyncio
async def test_assertion_fail_immediately():
    """Test if an assertion raises AND finishes, when it fails immediately."""

    events = []

    async def func(_stream):
        raise AssertionError()

    assertion = Assertion(events, func)
    task = assertion.start()
    # We do `await` here which causes the exception thrown inside the assertion
    # to be re-thrown:
    with pytest.raises(AssertionError):
        await task
    assert assertion.done
    assert assertion.failed


@pytest.mark.asyncio
async def test_assertion_consumes_one():
    """Test if an assertion will comsume all given events."""

    events = []

    async def func(stream):
        async for e in stream:
            return e

    assertion = Assertion(events, func)
    assertion.start()
    events.append(2)
    await assertion.update_events()
    assert assertion.accepted
    assert assertion.result == 2


@pytest.mark.asyncio
async def test_assertion_fails_on_event():
    """Test if an assertion is marked as failed when the result is an AssertionError."""

    events = [1]

    async def func(stream):
        async for _ in stream:
            assert False, "No events expected"

    assertion = Assertion(events, func)
    assertion.start()
    await assertion.update_events()
    assert assertion.failed
    assert isinstance(assertion.result, AssertionError)


@pytest.mark.asyncio
async def test_assertion_consumes_three():
    """Test if an assertion keeps state when events tickle in."""

    events = []

    async def func(stream):
        count = 0
        sum = 0
        async for e in stream:
            sum += e
            count += 1
            if count == 3:
                return sum

    assertion = Assertion(events, func)
    assertion.start()
    events.append(1)
    await assertion.update_events()
    assert not assertion.done

    events.append(2)
    await assertion.update_events()
    assert not assertion.done

    events.append(3)
    await assertion.update_events()
    assert assertion.accepted
    assert assertion.result == 6


@pytest.mark.asyncio
async def test_assertion_end_events():
    """Test if an assertion is accepted and done when no events are passed."""

    events = []

    async def func(stream):
        async for _ in stream:
            raise AssertionError("No events expected")
        return 44

    assertion = Assertion(events, func)
    assertion.start()
    assert not assertion.done

    await assertion.update_events(events_ended=True)
    assert assertion.accepted
    assert assertion.result == 44


@pytest.mark.asyncio
async def test_assertion_end_events_raises():
    """Test if an assertion raises when events_ended and there assertion is not met."""

    events = []

    async def func(stream):
        async for _ in stream:
            return
        raise AssertionError("Events expected")

    assertion = Assertion(events, func)
    assertion.start()
    assert not assertion.done

    await assertion.update_events(events_ended=True)
    assert assertion.failed
    assert isinstance(assertion.result, AssertionError)


@pytest.mark.asyncio
async def test_assertion_consumes_all():
    """Test if an assertion comsumes all events given to it."""

    events = []

    async def func(stream):
        _events = []
        async for e in stream:
            _events.append(e)
        return _events

    assertion = Assertion(events, func)
    assertion.start()

    for n in range(10):
        events.append(n)
        await assertion.update_events()

    await assertion.update_events(events_ended=True)
    assert assertion.done
    assert assertion.result == events


@pytest.mark.asyncio
async def test_events_ended_set():
    """Test if events_ended is set properly throughout the lifetime of an assertion."""

    events = [1]

    async def func(stream):

        assert not stream.events_ended

        async for _ in stream:
            assert not stream.events_ended

        assert stream.events_ended

    assertion = Assertion(events, func)
    assertion.start()
    await assertion.update_events()
    await assertion.update_events()
    await assertion.update_events(events_ended=True)
    assert assertion.done


@pytest.mark.asyncio
async def test_events_ended_not_set():
    """Test if events_ended is not set when the assertion breaks out of its loop."""

    events = [1]

    async def func(stream):

        assert not stream.events_ended

        async for _ in stream:
            assert not stream.events_ended
            break

        assert not stream.events_ended

    assertion = Assertion(events, func)
    assertion.start()
    await assertion.update_events()
    assert assertion.done


@pytest.mark.asyncio
async def test_past_events():
    """Test if `past_events` matches the events given to this assertion before."""

    events = []

    async def func(stream):

        _events = []

        async for e in stream:
            _events.append(e)
            assert _events == stream.past_events

        return _events

    assertion = Assertion(events, func)
    assertion.start()

    for n in range(3, 0, -1):
        events.append(n)
        await assertion.update_events()
    await assertion.update_events(events_ended=True)

    assert assertion.accepted
    assert assertion.result == [3, 2, 1]
