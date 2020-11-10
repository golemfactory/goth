"""`RequestorProbe` subclasses for controlling requestor nodes."""

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from openapi_activity_client import ExeScriptCommandResult, ExeScriptRequest
from openapi_market_client import AgreementProposal, Demand, Proposal
from openapi_payment_client import Acceptance, Allocation, Invoice

from goth.runner import step
from goth.runner.probe import Probe, RequestorProbe


logger = logging.getLogger(__name__)


class ActivityOperationsMixin:
    """Provides high-level steps that rely on Yagna Activity API."""

    @step()
    async def create_activity(self: RequestorProbe, agreement_id: str) -> str:
        """Call create_activity on the requestor activity api."""

        activity_id = self.activity.control.create_activity(agreement_id)
        return activity_id

    @step()
    async def call_exec(self: RequestorProbe, activity_id: str, exe_script: str) -> str:
        """Call call_exec on the requestor activity api."""

        script_request = ExeScriptRequest(exe_script)
        batch_id = self.activity.control.call_exec(activity_id, script_request)
        return batch_id

    @step()
    async def collect_results(
        self: RequestorProbe, activity_id: str, batch_id: str, num_results: int
    ) -> List[ExeScriptCommandResult]:
        """Call collect_results on the requestor activity api."""

        results: List[ExeScriptCommandResult] = []

        while len(results) < num_results:
            results = self.activity.control.get_exec_batch_results(
                activity_id, batch_id
            )
            await asyncio.sleep(1.0)
        return results

    @step()
    async def destroy_activity(self: RequestorProbe, activity_id: str) -> None:
        """Call destroy_activity on the requestor activity api."""

        self.activity.control.destroy_activity(activity_id)


class MarketOperationsMixin:
    """Provides high-level steps that rely on Yagna Market API."""

    @step()
    async def subscribe_demand(
        self: RequestorProbe, task_package: str, constraints: str
    ) -> Tuple[str, Demand]:
        """Call subscribe demand on the requestor market api."""

        demand = Demand(
            requestor_id=self.address,
            properties={
                "golem.node.id.name": "test1",
                "golem.srv.comp.expiration": int(
                    (datetime.now() + timedelta(minutes=10)).timestamp() * 1000
                ),
                "golem.srv.comp.task_package": task_package,
            },
            constraints=constraints,
        )

        subscription_id = self.market.subscribe_demand(demand)
        return subscription_id, demand

    @step()
    async def unsubscribe_demand(self: RequestorProbe, subscription_id: str) -> None:
        """Call unsubscribe demand on the requestor market api."""
        self.market.unsubscribe_demand(subscription_id)

    @step()
    async def wait_for_proposals(
        self: RequestorProbe,
        subscription_id: str,
        providers: Sequence[Probe],
        filter: Optional[Callable[[Proposal], bool]] = lambda p: True,
    ) -> List[Proposal]:
        """Call collect_offers on the requestor market api.

        Polls collect_offers continously until an offer from each of the given
        providers is received. Returns a list of the collected proposals.
        """
        proposals: List[Proposal] = []
        provider_ids = {p.address for p in providers}

        while len(proposals) < len(provider_ids):
            collected_offers = self.market.collect_offers(subscription_id)
            if collected_offers:
                logger.debug(
                    "collect_offers(%s). collected_offers=%r",
                    subscription_id,
                    collected_offers,
                )
                collected_proposals = [
                    offer.proposal
                    for offer in collected_offers
                    if (
                        offer.proposal.issuer_id in provider_ids
                        and filter(offer.proposal)
                    )
                ]
                proposals.extend(collected_proposals)
            else:
                logger.debug(
                    "Waiting for proposals. subscription_id=%s", subscription_id
                )
                await asyncio.sleep(1.0)

        return proposals

    @step()
    async def counter_proposal(
        self: RequestorProbe,
        subscription_id: str,
        demand: Demand,
        provider_proposal: Proposal,
    ) -> str:
        """Call counter_proposal_demand on the requestor market api."""

        proposal = Proposal(
            constraints=demand.constraints,
            properties=demand.properties,
            prev_proposal_id=provider_proposal.proposal_id,
        )

        counter_proposal = self.market.counter_proposal_demand(
            subscription_id=subscription_id,
            proposal_id=provider_proposal.proposal_id,
            proposal=proposal,
        )

        return counter_proposal

    @step()
    async def create_agreement(self: RequestorProbe, proposal: Proposal) -> str:
        """Call create_agreement on the requestor market api."""

        valid_to = str(datetime.utcnow() + timedelta(days=1)) + "Z"
        logger.debug(
            "Creating agreement, proposal_id=%s, valid_to=%s",
            proposal.proposal_id,
            valid_to,
        )
        agreement_proposal = AgreementProposal(
            proposal_id=proposal.proposal_id, valid_to=valid_to
        )

        agreement_id = self.market.create_agreement(agreement_proposal)
        return agreement_id

    @step()
    async def confirm_agreement(self: RequestorProbe, agreement_id: str) -> None:
        """Call confirm_agreement on the requestor market api."""
        self.market.confirm_agreement(agreement_id)


class PaymentOperationsMixin:
    """Provides high-level steps that rely on Yagna Payment API."""

    @step()
    async def gather_invoices(self: RequestorProbe, agreement_id: str) -> List[Invoice]:
        """Call gather_invoice on the requestor payment api."""

        invoices: List[Invoice] = []

        while not invoices:
            await asyncio.sleep(2.0)
            invoices = (
                self.payment.get_received_invoices()
            )  # to be replaced by requestor.events.waitUntil(InvoiceReceivedEvent)
            invoices = [inv for inv in invoices if inv.agreement_id == agreement_id]

        return invoices

    @step()
    async def pay_invoices(
        self: RequestorProbe, invoice_events: Iterable[Invoice]
    ) -> None:
        """Call accept_invoice on the requestor payment api."""

        for invoice_event in invoice_events:
            allocation = Allocation(
                total_amount=invoice_event.amount,
                spent_amount=0,
                remaining_amount=0,
                make_deposit=True,
            )
            allocation_result = self.payment.create_allocation(allocation)
            logger.debug("Created allocation. id=%s", allocation_result)

            acceptance = Acceptance(
                total_amount_accepted=invoice_event.amount,
                allocation_id=allocation_result.allocation_id,
            )
            self.payment.accept_invoice(invoice_event.invoice_id, acceptance)
            logger.debug("Accepted invoice. id=%s", invoice_event.invoice_id)


class RequestorProbeWithApiSteps(
    RequestorProbe,
    ActivityOperationsMixin,
    MarketOperationsMixin,
    PaymentOperationsMixin,
):
    """A testing interface for a Yagna requestor node, with all bells and whistles.

    This includes activity, market and payment API clients which can be used to
    directly control the requestor daemon, and higher-level steps that use those
    clients for making API calls.
    """
