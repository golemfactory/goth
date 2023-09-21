"""Integration test for agent-daemon communication through MITM proxy."""
import asyncio
from functools import partial
from pathlib import Path

import pytest


from goth.configuration import load_yaml
from goth.runner import Runner
from goth.runner.probe import RequestorProbe

from goth.assertions import EventStream
from goth.api_monitor.api_events import APIEvent, APIRequest


async def api_call_made(container_name: str, stream: EventStream[APIEvent]) -> bool:
    """Assert that an API call to `container_name` is made."""

    async for event in stream:
        if isinstance(event, APIRequest) and event.callee == f"{container_name}:daemon":
            return True
    raise AssertionError(f"No API call to {container_name} registered by proxy")


async def no_api_call_made(container_name: str, stream: EventStream[APIEvent]) -> bool:
    """Assert that no API call to `container_name` is made."""

    try:
        await api_call_made(container_name, stream)
    except AssertionError:
        return True
    raise AssertionError(f"API call to {container_name} registered by proxy")


@pytest.mark.asyncio
async def test_use_proxy(default_goth_config: Path, log_dir: Path) -> None:
    """Test if runner correctly sets up agent-daemon communication through proxy."""

    overrides = [
        (
            "nodes",
            [
                {"name": "requestor", "type": "Requestor", "use-proxy": True},
                {"name": "provider-1", "type": "VM-Wasm-Provider", "use-proxy": True},
                {"name": "provider-2", "type": "VM-Wasm-Provider", "use-proxy": False},
            ],
        )
    ]
    goth_config = load_yaml(default_goth_config, overrides)

    runner = Runner(
        base_log_dir=log_dir,
        compose_config=goth_config.compose_config,
    )

    requestor_assertion = runner.add_api_assertion(partial(api_call_made, "requestor"))
    runner.add_api_assertion(partial(api_call_made, "provider-1"))
    runner.add_api_assertion(partial(no_api_call_made, "provider-2"))

    async with runner(goth_config.containers):
        # Ceck it `use-proxy` flags in the config are correctly interpreted
        for probe in runner.probes:
            assert probe.uses_proxy == (probe.name != "provider-2")

        # Make an API call to the requestor daemon
        for probe in runner.probes:
            if isinstance(probe, RequestorProbe):
                await probe.api.payment.get_requestor_accounts()

        await requestor_assertion.wait_for_result(1.0)

        # Give provider agents time to make some API calls.
        await asyncio.sleep(10)
