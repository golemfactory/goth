"""End to end tests for requesting WASM tasks using goth REST API clients."""
import asyncio
import logging
from pathlib import Path
from typing import List

import pytest

from goth.address import (
    PROXY_HOST,
    YAGNA_REST_URL,
)
from goth.node import node_environment
from goth.runner import Runner
from goth.runner.container.payment import PaymentIdPool
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.provider import ProviderProbeWithLogSteps
from goth.runner.requestor import RequestorProbeWithApiSteps

from test.yagna.helpers.activity import run_activity
from test.yagna.helpers.negotiation import negotiate_agreements, DemandBuilder
from test.yagna.helpers.payment import pay_all

logger = logging.getLogger(__name__)


def _topology(
    assets_path: Path, payment_id_pool: PaymentIdPool
) -> List[YagnaContainerConfig]:
    """Define the topology of the test network."""

    # Nodes are configured to communicate via proxy
    provider_env = node_environment(
        rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
    )
    provider_env["IDLE_AGREEMENT_TIMEOUT"] = "5s"

    requestor_env = node_environment(
        rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
    )

    provider_volumes = {
        assets_path
        / "provider"
        / "presets.json": "/root/.local/share/ya-provider/presets.json"
    }

    return [
        YagnaContainerConfig(
            name="requestor",
            probe_type=RequestorProbeWithApiSteps,
            volumes={assets_path / "requestor": "/asset"},
            environment=requestor_env,
            payment_id=payment_id_pool.get_id(),
        ),
        YagnaContainerConfig(
            name="provider_1",
            probe_type=ProviderProbeWithLogSteps,
            environment=provider_env,
            payment_id=payment_id_pool.get_id(),
            volumes=provider_volumes,
            privileged_mode=True,
        ),
    ]


def build_demand(
    requestor: RequestorProbeWithApiSteps, runner: Runner, task_package_template
):
    """Simplifies creating demand."""

    task_package = task_package_template.format(
        web_server_addr=runner.host_address, web_server_port=runner.web_server_port
    )

    return (
        DemandBuilder(requestor)
        .props_from_template(task_package)
        .property("golem.srv.caps.multi-activity", True)
        .constraints(
            "(&(golem.com.pricing.model=linear)\
            (golem.srv.caps.multi-activity=true)\
            (golem.runtime.name=wasmtime))"
        )
        .build()
    )


# Provider is expected to break Agreement in time configured by
# variable: IDLE_AGREEMENT_TIMEOUT, if there are no Activities created.
@pytest.mark.asyncio
async def test_provider_idle_agreement(
    assets_path: Path,
    demand_constraints: str,
    exe_script: dict,
    payment_id_pool: PaymentIdPool,
    runner: Runner,
    task_package_template: str,
):
    """Test provider breaking idle Agreement."""

    async with runner(_topology(assets_path, payment_id_pool)):
        requestor = runner.get_probes(probe_type=RequestorProbeWithApiSteps)[0]
        providers = runner.get_probes(probe_type=ProviderProbeWithLogSteps)

        agreement_providers = await negotiate_agreements(
            requestor,
            build_demand(requestor, runner, task_package_template),
            providers,
        )

        await asyncio.sleep(5)
        await providers[0].wait_for_log(
            r"Breaking agreement .*, reason: No activity created", 10
        )

        await pay_all(requestor, agreement_providers)


# Provider is expected to break Agreement, if no new Activity was created
# after time configured by variable: IDLE_AGREEMENT_TIMEOUT.
# This test checks case, when Requestor already computed some Activities,
# but orphaned Agreement at some point.
@pytest.mark.asyncio
async def test_provider_idle_agreement_after_2_activities(
    assets_path: Path,
    demand_constraints: str,
    exe_script: dict,
    payment_id_pool: PaymentIdPool,
    runner: Runner,
    task_package_template: str,
):
    """Test provider breaking idle Agreement after 2 Activities were computed."""

    async with runner(_topology(assets_path, payment_id_pool)):
        requestor = runner.get_probes(probe_type=RequestorProbeWithApiSteps)[0]
        providers = runner.get_probes(probe_type=ProviderProbeWithLogSteps)

        agreement_providers = await negotiate_agreements(
            requestor,
            build_demand(requestor, runner, task_package_template),
            providers,
        )

        agreement_id, provider = agreement_providers[0]
        for i in range(0, 2):
            logger.info("Running activity %n-th time on %s", i, provider.name)
            await run_activity(requestor, provider, agreement_id, exe_script)

        await asyncio.sleep(5)
        await providers[0].wait_for_log(
            r"Breaking agreement .*, reason: No activity created", 10
        )

        await pay_all(requestor, agreement_providers)
