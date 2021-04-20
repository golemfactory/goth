"""Tests that zero-amount invoices are settled."""

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
from goth.runner.probe import ProviderProbe, RequestorProbe

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
            probe_type=RequestorProbe,
            environment=requestor_env,
            payment_id=payment_id_pool.get_id(),
        ),
        YagnaContainerConfig(
            name="provider",
            probe_type=ProviderProbe,
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
    payment_id_pool: PaymentIdPool,
    runner: Runner,
    task_package_template: str,
):
    """Test successful flow requesting WASM tasks with goth REST API client."""

    topology = _topology(assets_path, payment_id_pool)

    async with runner(topology):
        requestor = runner.get_probes(probe_type=RequestorProbe)[0]
        provider = runner.get_probes(probe_type=ProviderProbe)[0]

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

        logger.info("Processing proposal from %s", provider.name)

        counterproposal_id = await requestor.counter_proposal(
            subscription_id, demand, proposal
        )
        logger.info("Counter proposal %s", counterproposal_id)
        await provider.wait_for_proposal_accepted()

        new_proposals = await requestor.wait_for_proposals(
            subscription_id,
            (provider,),
            lambda proposal: proposal.prev_proposal_id == counterproposal_id,
        )

        # Here: Agreement
        agreement_id = await requestor.create_agreement(new_proposals[0])
        await requestor.confirm_agreement(agreement_id)
        await provider.wait_for_agreement_approved()

        await requestor.unsubscribe_demand(subscription_id)
        logger.info("Got agreement")

        #  Zero-amount invoice is issued when agreement is terminated
        #  without activity
        await requestor.wait_for_approval(agreement_id)
        await requestor.terminate_agreement(agreement_id, None)

        # Payment

        await provider.wait_for_invoice_sent()
        invoices = await requestor.gather_invoices(agreement_id)
        await requestor.pay_invoices(invoices)
        await provider.wait_for_invoice_paid()

        # verify requestor's invoice is settled
        invoice = (await requestor.gather_invoices(agreement_id))[0]
        assert invoice.amount == "0"
        assert invoice.status == InvoiceStatus.SETTLED
