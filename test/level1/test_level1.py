"""Level 1 test to be ran from pytest."""

import logging
from pathlib import Path
from string import Template
from typing import Dict, Optional

import pytest

from goth.address import (
    ACTIVITY_API_URL,
    MARKET_API_URL,
    MARKET_BASE_URL,
    PAYMENT_API_URL,
    PROXY_HOST,
    ROUTER_HOST,
    ROUTER_PORT,
    YAGNA_BUS_URL,
    YAGNA_REST_URL,
)
from goth.runner import Runner

from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.probe import Role

logger = logging.getLogger(__name__)


def node_environment(
    market_url_base: str = "", rest_api_url_base: str = ""
) -> Dict[str, str]:
    """Construct an environment for executing commands in a yagna docker container."""
    # Use custom base if given, default otherwise
    market_template_params = {"base": market_url_base} if market_url_base else {}

    daemon_env = {
        "CENTRAL_MARKET_URL": MARKET_API_URL.substitute(market_template_params),
        "CENTRAL_NET_HOST": f"{ROUTER_HOST}:{ROUTER_PORT}",
        "GSB_URL": YAGNA_BUS_URL.substitute(host="0.0.0.0"),
        "YAGNA_API_URL": YAGNA_REST_URL.substitute(host="0.0.0.0"),
        "RUST_LOG": "debug,trust_dns_proto=info",
    }
    node_env = daemon_env

    if rest_api_url_base:
        agent_env = {
            "YAGNA_MARKET_URL": MARKET_API_URL.substitute(base=rest_api_url_base),
            "YAGNA_ACTIVITY_URL": ACTIVITY_API_URL.substitute(base=rest_api_url_base),
            "YAGNA_PAYMENT_URL": PAYMENT_API_URL.substitute(base=rest_api_url_base),
        }
        node_env.update(agent_env)

    return node_env


VOLUMES = {
    Template("$assets_path"): "/asset",
    Template("$assets_path/presets.json"): "/presets.json",
}


LEVEL1_TOPOLOGY = [
    YagnaContainerConfig(
        name="requestor",
        role=Role.requestor,
        environment=node_environment(),
        volumes=VOLUMES,
    ),
    YagnaContainerConfig(
        name="provider_1",
        role=Role.provider,
        # Configure this provider node to communicate via proxy
        environment=node_environment(
            market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
            rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
        ),
        volumes=VOLUMES,
    ),
    # YagnaContainerConfig(
    #     name="provider_2",
    #     role=Role.provider,
    #     # Configure the second provider node to communicate via proxy
    #     environment=node_environment(
    #         market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
    #         rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
    #     ),
    #     volumes=VOLUMES,
    # ),
]


class TestLevel1:
    """TestCase running Level1Scenario."""

    @pytest.mark.asyncio
    async def test_level1(self, logs_path: Path, assets_path: Optional[Path]):
        """Test running Level1Scenario."""
        runner = Runner(
            LEVEL1_TOPOLOGY, "assertions.level1_assertions", logs_path, assets_path
        )

        all_providers = runner.get_probes_by_role(Role.provider)
        requestor = runner.get_probes_by_role(Role.requestor)

        all_providers.wait_for_offer_subscribed()
        subscription_id = requestor.subscribe_demand()
        proposal_1 = requestor.wait_for_proposal(subscription_id)
        requestor.counter_proposal(subscription_id, proposal_1)
        all_providers.wait_for_proposal_accepted()
        requestor.wait_for_proposal(subscription_id)
        # requestor.approve_agreement()
        # all_providers.wait_for_agreement_approved()
        # requestor.start_activity()
        # all_providers.wait_for_exeunit_started()
        # all_providers.wait_for_exeunit_finished()
        # all_providers.wait_for_invoice_sent()
        # requestor.pay_invoice()

        await runner.run_scenario()
