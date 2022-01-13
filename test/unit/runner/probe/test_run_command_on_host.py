"""Tests for the method Probe.run_command_on_host."""
import asyncio
import os
import pytest
from unittest.mock import MagicMock

from goth.address import YAGNA_BUS_URL, YAGNA_REST_URL, YAGNA_REST_PORT
import goth.runner.container.yagna
from goth.runner.probe import RequestorProbe

CONTAINER_REST_PORT = 6006


async def env_lines_to_dict(lines):
    """Convert the lines received from the `env` command into a dictionary."""
    # The monitor should guarantee that we don't skip any events
    assert len(lines.past_events) == 0, lines.past_events
    env = {}
    async for line in lines:
        tokens = line.split("=", 1)
        if len(tokens) == 2:
            env[tokens[0]] = tokens[1]
    return env


def mock_probe(monkeypatch):
    """Get a mocked `RequestorProbe`."""

    runner = MagicMock()
    docker_client = MagicMock()
    container_config = MagicMock(use_proxy=False)
    log_config = MagicMock()

    monkeypatch.setattr(goth.runner.probe, "YagnaContainer", MagicMock(spec="ports"))
    monkeypatch.setattr(goth.runner.probe, "Cli", MagicMock(spec="yagna"))
    monkeypatch.setattr(RequestorProbe, "app_key", "0xcafebabe")

    probe = RequestorProbe(
        runner=runner,
        client=docker_client,
        config=container_config,
        log_config=log_config,
    )
    probe.container.ports = {YAGNA_REST_PORT: CONTAINER_REST_PORT}
    return probe


@pytest.mark.asyncio
async def test_run_command_on_host(monkeypatch):
    """Test if the method `run_command_on_host` works as expected."""

    probe = mock_probe(monkeypatch)

    async with probe.run_command_on_host(
        "/usr/bin/env",
        env=os.environ,
        get_process_monitor=True,
    ) as (_task, monitor, process_monitor):
        assertion = monitor.add_assertion(env_lines_to_dict)
        proc: asyncio.subprocess.Process = await process_monitor.get_process()

    assert await proc.wait() == 0

    result = await assertion.wait_for_result(timeout=1)

    assert result["YAGNA_APPKEY"] == probe.app_key
    assert result["YAGNA_API_URL"] == YAGNA_REST_URL.substitute(
        host="127.0.0.1", port=CONTAINER_REST_PORT
    )
    assert result["GSB_URL"] == YAGNA_BUS_URL.substitute(host=None)

    # Let's make sure that another command can be run without problems
    # (see https://github.com/golemfactory/goth/issues/484).
    async with probe.run_command_on_host("/bin/echo eChO", env=os.environ) as (
        _task,
        monitor,
    ):

        await monitor.wait_for_pattern(".*eChO", timeout=10)
