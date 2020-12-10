"""End to end tests for requesting WASM tasks using goth REST API clients."""

import asyncio
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
from goth.node import node_environment
from goth.runner import Runner
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
            subnet="goth"
        ),
        YagnaContainerConfig(
            name="provider_2",
            probe_type=ProviderProbeWithLogSteps,
            environment=provider_env,
            volumes=provider_volumes,
            privileged_mode=True,
            subnet="goth"
        ),
    ]



## ASSERTIONS #################################################

import json

from goth.api_monitor.api_events import APIEvent, APIResponse
from goth.assertions.common import (
    APIEvents,
)
from goth.assertions.operators import eventually


def contains_activity_event(event: APIEvent, event_type: str) -> bool:
    if (
        isinstance(event, APIResponse)
        and event.request.path.startswith("/activity-api/v1/events?")
        and event.status_code == 200
    ):
        body = json.loads(event.content)
        if any(e["eventType"] == event_type for e in body):
            return True
    return False


async def assert_activity_started(stream: APIEvents) -> None:

    event = await eventually(stream, lambda e: contains_activity_event(e, "CreateActivity"))
    if event:
        print("\033[32;1m🙂 Activity started!\033[0m")
    else:
        print("\033[31;1m🙁 Activity not started!\033[0m")
        assert False


async def assert_activity_started_destroyed(stream: APIEvents) -> None:

    await assert_activity_started(stream)

    event = await eventually(stream, lambda e: contains_activity_event(e, "DestroyActivity"))
    if event:
        print("\033[32;1m🙂 Activity destroyed!\033[0m")
    else:
        print("\033[31;1m🙁 Activity not destroyed!\033[0m")
        assert False

###################################################

@pytest.fixture
def cancellation_callback() -> Callable[[], None]:
    return lambda: logging.getLogger("goth.runner").info("The runner was cancelled")


@pytest.mark.asyncio
async def test_e2e_vm_interactive(
    assets_path: Path,
    demand_constraints: str,
    payment_id_pool: PaymentIdPool,
    runner: Runner,
):
    topology = _topology(assets_path, payment_id_pool)

    async with runner(topology):

        runner.proxy.monitor.add_assertion(assert_activity_started_destroyed)

        providers = runner.get_probes(probe_type=ProviderProbeWithLogSteps)
        requestor = runner.get_probes(probe_type=RequestorProbe)[0]

        print("\n\033[33;1mNow run your requestor agent as follows:\n")
        print(
            f"$  YAGNA_APPKEY={requestor.app_key} "
            f"YAGNA_API_URL=http://{requestor.ip_address}:{YAGNA_REST_PORT} "
            f"GSB_URL=tcp://{requestor.ip_address}:{YAGNA_BUS_PORT} "
            f"examples/blender/blender.py --subnet {providers[0].subnet}"
        )
        print("\nPress Ctrl+C at any moment to stop the test harness.\033[0m")

        while True:
            await asyncio.sleep(5)
            runner.check_assertion_errors()
