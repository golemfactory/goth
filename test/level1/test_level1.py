"""Level 1 test to be ran from pytest."""

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
from goth.runner.probe import Provider, Requestor

logger = logging.getLogger(__name__)

LEVEL1_TOPOLOGY = [
    YagnaContainerConfig(
        name="requestor",
        role=Requestor,
        environment=node_environment(account_list="/asset/key/001-accounts.json"),
        key_file="/asset/key/001.json",
        volumes=VOLUMES,
    ),
    YagnaContainerConfig(
        name="provider_1",
        role=Provider,
        # Configure this provider node to communicate via proxy
        environment=node_environment(
            market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
            rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
        ),
        volumes=VOLUMES,
    ),
    YagnaContainerConfig(
        name="provider_2",
        role=Provider,
        # Configure the second provider node to communicate via proxy
        environment=node_environment(
            market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
            rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
        ),
        volumes=VOLUMES,
    ),
]


class TestLevel1:
    """TestCase running Level1Scenario."""

    @pytest.mark.asyncio
    async def test_level1(self, logs_path: Path, assets_path: Optional[Path]):
        """Test running Level1Scenario."""
        runner = Runner(
            LEVEL1_TOPOLOGY, "assertions.level1_assertions", logs_path, assets_path
        )

        providers = runner.get_probes(role=Provider)
        requestor = runner.get_probes(role=Requestor)

        requestor.init_payment()

        # Market
        providers.wait_for_offer_subscribed()
        subscription_id = requestor.subscribe_demand()
        proposals = requestor.wait_for_proposals(subscription_id, providers._probes)
        requestor.counter_proposals(subscription_id, proposals)
        providers.wait_for_proposal_accepted()
        requestor.wait_for_proposals(subscription_id, providers._probes)
        agreement_ids = requestor.create_agreements(proposals)
        requestor.confirm_agreements(agreement_ids)
        providers.wait_for_agreement_approved()
        requestor.unsubscribe_demand(subscription_id)

        # Activity
        activity_ids = requestor.create_activities(agreement_ids)
        providers.wait_for_activity_created()
        activity_batches = requestor.call_exec(activity_ids)
        providers.wait_for_exeunit_started()
        requestor.collect_results(activity_batches)
        requestor.destroy_activities(activity_ids)
        providers.wait_for_exeunit_finished()

        # Payment
        providers.wait_for_invoice_sent()
        invoices = requestor.gather_invoices(agreement_ids)
        requestor.pay_invoices(invoices)
        providers.wait_for_invoice_paid()

        await runner.run_scenario()
