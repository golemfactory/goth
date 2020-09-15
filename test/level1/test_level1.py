"""Level 1 test to be ran from pytest."""

import json
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
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.probe import ProviderProbe, Provider, Requestor
from goth.runner.provider import ProviderProbeWithLogSteps
from goth.runner.requestor import ApiEnabledRequestorProbe, RequestorProbeWithApiSteps
from goth.runner.simple import SimpleRunner
from goth.runner.sequence import ProbeStepBuilder, SequenceRunner

logger = logging.getLogger(__name__)


LEVEL1_TOPOLOGY = [
    YagnaContainerConfig(
        name="requestor",
        # TODO: `role` should be replaced by something like `probe_class`
        role=ApiEnabledRequestorProbe,
        environment=node_environment(account_list="/asset/key/001-accounts.json"),
        key_file="/asset/key/001.json",
        volumes=VOLUMES,
    ),
    YagnaContainerConfig(
        name="provider_1",
        role=ProviderProbe,
        # Configure this provider node to communicate via proxy
        environment=node_environment(
            market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
            rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
        ),
        volumes=VOLUMES,
    ),
    YagnaContainerConfig(
        name="provider_2",
        role=ProviderProbe,
        # Configure the second provider node to communicate via proxy
        environment=node_environment(
            market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
            rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
        ),
        volumes=VOLUMES,
    ),
]


@pytest.mark.asyncio
async def test_level1_steps(logs_path: Path, assets_path: Optional[Path]):
    """Test running Level1Scenario."""

    runner = SequenceRunner(
        LEVEL1_TOPOLOGY, "assertions.level1_assertions", logs_path, assets_path
    )

    providers: ProbeStepBuilder = runner.get_builder(role=Provider)
    requestor: ProbeStepBuilder = runner.get_builder(role=Requestor)

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


@pytest.mark.asyncio
async def test_level1_simple(logs_path: Path, assets_path: Optional[Path]):
    """Test running Level1Scenario with SimpleRunner."""

    topology = [
        YagnaContainerConfig(
            name="requestor",
            role=RequestorProbeWithApiSteps,
            environment=node_environment(account_list="/asset/key/001-accounts.json"),
            key_file="/asset/key/001.json",
            volumes=VOLUMES,
        ),
        YagnaContainerConfig(
            name="provider_1",
            role=ProviderProbeWithLogSteps,
            # Configure this provider node to communicate via proxy
            environment=node_environment(
                market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
                rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
            ),
            volumes=VOLUMES,
        ),
        YagnaContainerConfig(
            name="provider_2",
            role=ProviderProbeWithLogSteps,
            # Configure the second provider node to communicate via proxy
            environment=node_environment(
                market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
                rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
            ),
            volumes=VOLUMES,
        ),
    ]

    # TODO: provide the exe script in a fixture?
    if assets_path is None:
        level1_dir = Path(__file__).parent
        level0_dir = level1_dir.parent / "level0"
        assets_path = level0_dir / "asset"
    exe_script_path = Path(assets_path / "exe_script.json")
    exe_script = exe_script_path.read_text()

    async with SimpleRunner(
        topology, "assertions.level1_assertions", logs_path, assets_path
    ) as runner:

        requestor = runner.get_probes(name="requestor")[0]
        assert isinstance(requestor, RequestorProbeWithApiSteps)

        provider_1, provider_2 = runner.get_probes(role=Provider)
        assert isinstance(provider_1, ProviderProbeWithLogSteps)
        assert isinstance(provider_2, ProviderProbeWithLogSteps)

        providers = (provider_1, provider_2)

        # Market

        for provider in providers:
            await provider.wait_for_offer_subscribed()

        subscription_id, demand = await requestor.subscribe_demand()

        proposals = await requestor.wait_for_proposals(subscription_id, providers)
        logger.info("Collected %s proposals", len(proposals))

        agreement_providers = []

        for proposal in proposals:
            provider = next(p for p in providers if p.address == proposal.issuer_id)
            logger.info("Processing proposal from %s", provider.name)

            counterproposal_id = await requestor.counter_proposal(
                subscription_id, demand, proposal
            )
            await provider.wait_for_proposal_accepted()

            new_proposals = await requestor.wait_for_proposals(
                subscription_id, (provider,)
            )
            new_proposal = new_proposals[0]
            assert new_proposal.prev_proposal_id == counterproposal_id

            agreement_id = await requestor.create_agreement(new_proposal)
            await requestor.confirm_agreement(agreement_id)
            await provider.wait_for_agreement_approved()
            agreement_providers.append((agreement_id, provider))

        await requestor.unsubscribe_demand(subscription_id)
        logger.info("Got %s agreements", len(agreement_providers))

        #  Activity

        num_commands = len(json.loads(exe_script))

        for agreement_id, provider in agreement_providers:
            logger.info("Running activity on %s", provider.name)
            activity_id = await requestor.create_activity(agreement_id)
            await provider.wait_for_activity_created()
            batch_id = await requestor.call_exec(activity_id, exe_script)
            await provider.wait_for_exeunit_started()
            await requestor.collect_results(
                activity_id, batch_id, num_commands, timeout=30
            )
            await requestor.destroy_activity(activity_id)
            await provider.wait_for_exeunit_finished()

        # Payment

        for agreement_id, provider in agreement_providers:
            await provider.wait_for_invoice_sent()
            invoices = await requestor.gather_invoices(agreement_id)
            assert all(inv.agreement_id == agreement_id for inv in invoices)
            # TODO:
            await requestor.pay_invoices(invoices)
            await provider.wait_for_invoice_paid()

    logger.info("Test finished")
