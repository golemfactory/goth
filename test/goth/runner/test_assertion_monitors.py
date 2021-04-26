"""Unit tests related to the use of assertion monitors in Runner."""

import asyncio
from pathlib import Path
import tempfile
from unittest.mock import Mock

import pytest

from goth.assertions.monitor import EventMonitor
from goth.runner import Runner, TemporalAssertionError


@pytest.mark.asyncio
async def test_check_assertions(caplog):
    """Test the `Runner.check_assertion_errors()` method."""

    runner = Runner(
        base_log_dir=Path(tempfile.mkdtemp()),
        compose_config=Mock(),
    )

    async def assertion(events):
        async for _ in events:
            break
        async for _ in events:
            raise AssertionError("Just failing")

    idle_monitor = EventMonitor()
    idle_monitor.start()
    busy_monitor = EventMonitor()
    busy_monitor.add_assertion(assertion)
    busy_monitor.start()

    await asyncio.sleep(0.1)
    runner.check_assertion_errors(idle_monitor, busy_monitor)

    await busy_monitor.add_event(1)
    await asyncio.sleep(0.1)
    runner.check_assertion_errors(idle_monitor, busy_monitor)

    await busy_monitor.add_event(2)
    await asyncio.sleep(0.1)
    # Assertion failure should be logged at this point
    assert any(record.levelname == "ERROR" for record in caplog.records)
    # And `check_assertion_errors()` should raise an exception
    with pytest.raises(TemporalAssertionError):
        runner.check_assertion_errors(idle_monitor, busy_monitor)

    await busy_monitor.stop()
    await idle_monitor.stop()
    with pytest.raises(TemporalAssertionError):
        runner.check_assertion_errors(idle_monitor, busy_monitor)
