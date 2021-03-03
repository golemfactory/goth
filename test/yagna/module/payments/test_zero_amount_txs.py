"""Tests that zero-amount invoices are settled."""

import logging
from pathlib import Path
from typing import List

import pytest
import time
from asyncio import sleep

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

from ya_market.exceptions import ApiException
from ya_payment import InvoiceStatus

logger = logging.getLogger(__name__)


def _topology(
    assets_path: Path, payment_id_pool: PaymentIdPool
) -> List[YagnaContainerConfig]:
    # Nodes are configured to communicate via proxy
    provider_env = node_environment(
        rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
    )
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
            name="provider",
            probe_type=ProviderProbeWithLogSteps,
            environment=provider_env,
            # https://github.com/golemfactory/goth/issues/410
            privileged_mode=True,
            volumes=provider_volumes,
        ),
    ]


@pytest.mark.asyncio
async def test_zero_amount_invoice_is_settled(
    assets_path: Path,
    demand_constraints: str,
    exe_script: dict,
    payment_id_pool: PaymentIdPool,
    runner: Runner,
    task_package_template: str,
):
    """Test successful flow requesting WASM tasks with goth REST API client."""

    topology = _topology(assets_path, payment_id_pool)

    async with runner(topology):
        requestor = runner.get_probes(probe_type=RequestorProbeWithApiSteps)[0]
        provider = runner.get_probes(probe_type=ProviderProbeWithLogSteps)[0]

        # Market

        await provider.wait_for_offer_subscribed()

        task_package = task_package_template.format(
            web_server_addr=runner.host_address, web_server_port=runner.web_server_port
        )

        subscription_id, demand = await requestor.subscribe_template_demand(
            task_package, demand_constraints
        )

        proposal = (
            await requestor.wait_for_proposals(
                subscription_id,
                [provider],
                lambda proposal: (
                    proposal.properties.get("golem.runtime.name") == "wasmtime"
                ),
            )
        )[0]
        logger.info("Collected the proposal")

        logger.info("Processing proposal from %s", provider.name)

        # HINT: According to @kubam this is needed.
        counterproposal_id = await requestor.counter_proposal(
            subscription_id, demand, proposal
        )
        await provider.wait_for_proposal_accepted()

        new_proposals = await requestor.wait_for_proposals(subscription_id, (provider,))
        new_proposal = new_proposals[0]
        assert new_proposal.prev_proposal_id == counterproposal_id

        # Here: Agreement
        agreement_id = await requestor.create_agreement(new_proposal)
        await requestor.confirm_agreement(agreement_id)
        await provider.wait_for_agreement_approved()

        await requestor.unsubscribe_demand(subscription_id)
        logger.info("Got agreement")

        #  Zero-amount invoice is issued when agreement is terminated without activity
        await wait_for_agreement_termination(requestor, provider, agreement_id)

        # Payment

        await provider.wait_for_invoice_sent()
        invoices = await requestor.gather_invoices(agreement_id)
        await requestor.pay_invoices(invoices)
        await provider.wait_for_invoice_paid()

        # verify requestor's invoice is settled
        invoice = (await requestor.gather_invoices(agreement_id))[0]
        assert invoice.amount == "0"
        assert invoice.status == InvoiceStatus.SETTLED

        # verify the provider invoice is settled
        # TODO: Expose PaymentOperationMixin from Provider-based probe
        # pseudo-code:
        # invoice2 = (await providers.gather_invoices(agreement_id))[0]
        # assert invoice2.amount == "0"
        # assert invoice2.status == InvoiceStatus.SETTLED


async def wait_for_agreement_termination(requestor, provider, agreement_id):
    """Wait for agreement termination with retries in a given timespan."""

    logger.info("Waiting for the agreement termination... ")
    total_retry_time_seconds = 30
    start = time.time()
    while True:
        assert total_retry_time_seconds > time.time() - start, "Retries time exceeded"
        try:
            await requestor.terminate_agreement(agreement_id, None)
            break
        except ApiException:
            logger.info("Retry: Waiting for agreement termination")
            await sleep(1)
    await provider.wait_for_agreement_terminated()
