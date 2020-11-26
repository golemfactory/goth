"""End to end tests for requesting WASM tasks using goth REST API clients."""

import json
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
from goth.runner.container.compose import ComposeConfig
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.provider import ProviderProbeWithLogSteps
from goth.runner.requestor import RequestorProbeWithApiSteps

from test.yagna.helpers.negotiation import negotiate_agreements, DemandBuilder
from test.yagna.helpers.payment import pay_all

logger = logging.getLogger(__name__)


def topology(assets_path: Path) -> List[YagnaContainerConfig]:
    """Define the topology of the test network."""

    # Nodes are configured to communicate via proxy
    provider_env = node_environment(
        rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
    )
    requestor_env = node_environment(
        rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
        account_list="/asset/key/001-accounts.json",
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
            key_file="/asset/key/001.json",
        ),
        YagnaContainerConfig(
            name="provider_1",
            probe_type=ProviderProbeWithLogSteps,
            environment=provider_env,
            volumes=provider_volumes,
        ),
    ]


# Tests running multiple activities on single Provider.
# In this case Requestor is responsible for terminating Agreement.
# Provider should listen
@pytest.mark.asyncio
async def test_provider_multi_activity(
    logs_path: Path,
    assets_path: Path,
    exe_script: dict,
    compose_config: ComposeConfig,
    task_package_template: str,
    demand_constraints: str,
):
    """Test successful flow requesting WASM tasks with goth REST API client."""

    async with Runner(
        api_assertions_module="test.yagna.assertions.e2e_wasm_assertions",
        assets_path=assets_path,
        compose_config=compose_config,
        logs_path=logs_path,
        topology=topology(assets_path),
    ) as runner:

        requestor = runner.get_probes(probe_type=RequestorProbeWithApiSteps)[0]
        providers = runner.get_probes(probe_type=ProviderProbeWithLogSteps)

        # Market
        task_package = task_package_template.format(
            web_server_addr=runner.host_address, web_server_port=runner.web_server_port
        )

        demand = (
            DemandBuilder(requestor)
            .props_from_template(task_package)
            .property("golem.srv.comp.multi-activity", True)
            .constraints(
                "(&(golem.com.pricing.model=linear)(golem.inf.multi-activity=true))"
            )
            .build()
        )
        agreement_providers = await negotiate_agreements(
            requestor,
            demand,
            providers,
        )

        #  Activity
        num_commands = len(exe_script)

        for agreement_id, provider in agreement_providers:
            for i in range(0, 3):
                logger.info("Running activity %n-th time on %s", i, provider.name)
                activity_id = await requestor.create_activity(agreement_id)
                await provider.wait_for_exeunit_started()
                batch_id = await requestor.call_exec(
                    activity_id, json.dumps(exe_script)
                )
                await requestor.collect_results(
                    activity_id, batch_id, num_commands, timeout=30
                )
                await requestor.destroy_activity(activity_id)
                await provider.wait_for_exeunit_finished()

            await requestor.terminate_agreement(agreement_id, None)
            await provider.wait_for_agreement_terminated()

        # Payment
        await pay_all(requestor, agreement_providers)
