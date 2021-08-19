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
    """Assert that an API call to `container_name` has been made in the past."""

    for event in stream.past_events:
        if isinstance(event, APIRequest) and event.callee == f"{container_name}:daemon":
            return True
    raise AssertionError(f"No API call to {container_name} registered by proxy")


async def no_api_call_made(container_name: str, stream: EventStream[APIEvent]) -> bool:
    """Assert that no API call to `container_name` has been made in the past."""

    try:
        await api_call_made(container_name, stream)
    except AssertionError:
        return True
    raise AssertionError(f"API call to {container_name} registered by proxy")


@pytest.mark.asyncio
async def test_use_proxy(default_goth_config: Path, log_dir: Path) -> None:
    """Test if runner correctly sets up agent-deamon communication through proxy."""

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

    async with runner(goth_config.containers):

        # Ceck it `use-proxy` flags in the config are correctly interpreted
        for probe in runner.probes:
            assert probe.uses_proxy == (probe.name != "provider-2")

        # Make an API call to the requestor daemon
        for probe in runner.probes:
            if isinstance(probe, RequestorProbe):
                await probe.api.payment.get_requestor_accounts()

        # Give provider agents time to make some API calls
        await asyncio.sleep(10)

        # Assert that API calls were intercepted for probes configured to use proxy
        # and not intercepted for the probe configured not to use it
        for probe in runner.probes:
            if probe.uses_proxy:
                assertion = runner.proxy.monitor.add_assertion(
                    partial(api_call_made, probe.container.name),
                    name=f"api_call_made({probe.container.name})",
                )
            else:
                assertion = runner.proxy.monitor.add_assertion(
                    partial(no_api_call_made, probe.container.name),
                    name=f"no_api_call_made({probe.container.name})",
                )
            assert await assertion.wait_for_result()
