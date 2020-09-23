"""Level 0 test to be ran from pytest."""

import logging
from pathlib import Path
from typing import Optional

import pytest

from goth.address import (
    MARKET_BASE_URL,
    PROXY_HOST,
    YAGNA_REST_URL,
)
from goth.node import node_environment, VOLUMES
from goth.runner import Runner
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.probe import ProviderProbe, RequestorProbeWithAgent
from goth.runner.provider import ProviderProbeWithLogSteps

logger = logging.getLogger(__name__)

LEVEL0_TOPOLOGY = [
    YagnaContainerConfig(
        name="requestor",
        probe_type=RequestorProbeWithAgent,
        environment=node_environment(account_list="/asset/key/001-accounts.json"),
        volumes=VOLUMES,
        key_file="/asset/key/001.json",
    ),
    YagnaContainerConfig(
        name="provider_1",
        probe_type=ProviderProbe,
        # Configure this provider node to communicate via proxy
        environment=node_environment(
            market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
            rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
        ),
        volumes=VOLUMES,
    ),
    YagnaContainerConfig(
        name="provider_2",
        probe_type=ProviderProbe,
        # Configure the second provider node to communicate via proxy
        environment=node_environment(
            market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
            rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
        ),
        volumes=VOLUMES,
    ),
]


@pytest.mark.asyncio
async def test_level0(logs_path: Path, assets_path: Optional[Path]):
    """Test running level 0 scenario."""

    async with Runner(
        LEVEL0_TOPOLOGY, "assertions.level0_assertions", logs_path, assets_path
    ) as runner:

        providers = runner.get_probes(probe_type=ProviderProbe)

        steps = [
            ProviderProbeWithLogSteps.wait_for_offer_subscribed,
            ProviderProbeWithLogSteps.wait_for_proposal_accepted,
            ProviderProbeWithLogSteps.wait_for_agreement_approved,
            ProviderProbeWithLogSteps.wait_for_exeunit_started,
            ProviderProbeWithLogSteps.wait_for_exeunit_finished,
            ProviderProbeWithLogSteps.wait_for_invoice_sent,
            ProviderProbeWithLogSteps.wait_for_invoice_paid,
        ]

        for step in steps:
            for provider in providers:
                await step(provider)
