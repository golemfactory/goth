"""End to end tests for requesting WASM tasks using goth REST API clients."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Callable, List

import pytest

from goth.address import (
    PROXY_HOST,
    YAGNA_REST_URL,
    YAGNA_BUS_PORT,
    YAGNA_REST_PORT,
)
from goth.api_monitor.api_events import APIEvent, APIRequest, APIResponse
from goth.assertions.common import APIEvents
from goth.assertions.operators import eventually
from goth.node import node_environment
from goth.runner import Runner, TestFailure
from goth.runner.container.payment import PaymentIdPool
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.probe import RequestorProbe
from goth.runner.provider import ProviderProbeWithLogSteps


logger = logging.getLogger(__name__)


requestor_env = node_environment(
    rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
    account_list="/asset/key/001-accounts.json",
)


def _topology(
    assets_path: Path, payment_id_pool: PaymentIdPool
) -> List[YagnaContainerConfig]:
    """Define the topology of the test network."""

    # Nodes are configured to communicate via proxy
    provider_env = node_environment(
        rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
    )
    requestor_env = node_environment(
        # TODO: not required, since the agent does not run in a container
        rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
    )

    provider_volumes = {
        assets_path
        / "provider"
        / "presets.json": "/root/.local/share/ya-provider/presets.json",
        assets_path
        / "provider"
        / "hardware.json": "/root/.local/share/ya-provider/hardware.json",
        assets_path
        / "provider"
        / "images": "/root/.local/share/ya-provider/exe-unit/cache/tmp",
    }

    return [
        YagnaContainerConfig(
            name="requestor",
            probe_type=RequestorProbe,
            volumes={assets_path / "requestor": "/asset"},
            environment=requestor_env,
            payment_id=payment_id_pool.get_id(),
        ),
        YagnaContainerConfig(
            name="provider_1",
            probe_type=ProviderProbeWithLogSteps,
            environment=provider_env,
            volumes=provider_volumes,
            privileged_mode=True,
            subnet="goth",
        ),
        YagnaContainerConfig(
            name="provider_2",
            probe_type=ProviderProbeWithLogSteps,
            environment=provider_env,
            volumes=provider_volumes,
            privileged_mode=True,
            subnet="goth",
        ),
    ]


# ASSERTIONS #################################################


def _contains_activity_event(event: APIEvent, event_type: str) -> bool:
    if (
        isinstance(event, APIResponse)
        and event.request.path.startswith("/activity-api/v1/events?")
        and event.status_code == 200
    ):
        body = json.loads(event.content)
        if any(e["eventType"] == event_type for e in body):
            return True
    return False


async def _assert_activity_started(stream: APIEvents) -> None:

    event = await eventually(
        stream, lambda e: _contains_activity_event(e, "CreateActivity")
    )
    if event:
        print("\033[32;1m🙂 Activity started!\033[0m")
    else:
        print("\033[31;1m🙁 Activity not started!\033[0m")
        assert False


async def _assert_activity_started_destroyed(stream: APIEvents) -> None:

    await _assert_activity_started(stream)

    event = await eventually(
        stream, lambda e: _contains_activity_event(e, "DestroyActivity")
    )
    if event:
        print("\033[32;1m🙂 Activity destroyed!\033[0m")
    else:
        print("\033[31;1m🙁 Activity not destroyed!\033[0m")
        assert False


# This will fail, it's just to check how assertion failures are reported
async def _assert_activity_api_not_called(stream: APIEvents) -> None:

    async for event in stream:
        if isinstance(event, APIRequest):
            assert not event.path.startswith("/activity-api/")


###################################################


@pytest.fixture
def cancellation_callback() -> Callable[[], None]:
    """Report that the runner was cancelled, do not fail the test."""

    logger = logging.getLogger("goth.runner.interactive")
    return lambda: logger.info("The runner was cancelled")


@pytest.fixture
def test_failure_callback() -> Callable[[TestFailure], None]:
    """Report the failure, do not fail the test."""

    logger = logging.getLogger("goth.runner.interactive")
    return lambda error: logger.error(
        "The runner was stopped due to test failure: {error}"
    )


@pytest.mark.asyncio
async def test_e2e_vm_interactive(
    assets_path: Path,
    demand_constraints: str,
    payment_id_pool: PaymentIdPool,
    runner: Runner,
):
    topology = _topology(assets_path, payment_id_pool)

    async with runner(topology):

        providers = runner.get_probes(probe_type=ProviderProbeWithLogSteps)
        requestor = runner.get_probes(probe_type=RequestorProbe)[0]

        # Some test steps may be included in the interactive test as well
        for provider in providers:
            await provider.wait_for_offer_subscribed(timeout=10)

        print("\n\033[33;1mNow run your requestor agent as follows:\n")
        print(
            f"$  YAGNA_APPKEY={requestor.app_key} "
            f"YAGNA_API_URL=http://{requestor.ip_address}:{YAGNA_REST_PORT} "
            f"GSB_URL=tcp://{requestor.ip_address}:{YAGNA_BUS_PORT} "
            f"examples/blender/blender.py --subnet {providers[0].subnet}"
        )
        print("\nPress Ctrl+C at any moment to stop the test harness.\033[0m\n")

        # Assertions may be added at any point. They have to be checked
        # periodically by calling `runner.check_assertion_errors()`.
        # They will be also checked automatically on runner exit.
        runner.proxy.monitor.add_assertion(_assert_activity_started_destroyed)
        # runner.proxy.monitor.add_assertion(_assert_activity_api_not_called)

        while True:
            await asyncio.sleep(5)
            runner.check_assertion_errors()
