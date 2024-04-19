"""Probe mixins containing high-level steps."""

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import (
    Callable,
    Iterable,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TYPE_CHECKING,
)

from ya_activity import ExeScriptCommandResult, ExeScriptRequest, ApiException
from ya_market import AgreementProposal, Demand, DemandOfferBase, Proposal
from ya_payment import Acceptance, Allocation, Invoice

from goth.node import DEFAULT_SUBNET
from goth.payment_config import PaymentConfig
from goth.runner.step import retry_on, step

if TYPE_CHECKING:
    from goth.runner.probe import Probe
    from goth.runner.probe.agent import AgentComponent
    from goth.runner.probe.rest_client import RestApiComponent

logger = logging.getLogger(__name__)


class ProbeProtocol(Protocol):
    """Protocol class representing the probe interface in mixins.

    This is mainly to fix mypy errors when using `Probe` directly as `self` type.
    """

    agents: "List[AgentComponent]"
    """List of agent components that will be started as part of a probe."""

    api: "RestApiComponent"
    """REST API probe component."""

    name: str
    """Name of the probe container."""

    payment_config: PaymentConfig
    """Payment configuration used for the probe's yagna node."""


class ActivityApiMixin:
    """Probe mixin providing high-level test steps which use yagna activity API."""

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def create_activity(self: ProbeProtocol, agreement_id: str) -> str:
        """Call create_activity on the activity api."""

        activity_id = await self.api.activity.control.create_activity(agreement_id)
        return activity_id

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def call_exec(self: ProbeProtocol, activity_id: str, exe_script: str) -> str:
        """Call call_exec on the activity api."""

        script_request = ExeScriptRequest(exe_script)
        batch_id = await self.api.activity.control.call_exec(activity_id, script_request)
        return batch_id

    @step(120.0)
    @retry_on(ApiException, 60.0)
    async def collect_results(
        self: ProbeProtocol, activity_id: str, batch_id: str, num_results: int
    ) -> List[ExeScriptCommandResult]:
        """Call collect_results on the activity api."""

        results: List[ExeScriptCommandResult] = []

        while len(results) < num_results:
            results = await self.api.activity.control.get_exec_batch_results(
                activity_id, batch_id, timeout=1
            )
            await asyncio.sleep(1.0)
        return results

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def destroy_activity(self: ProbeProtocol, activity_id: str) -> None:
        """Call destroy_activity on the activity api."""

        await self.api.activity.control.destroy_activity(activity_id)


class MarketApiMixin:
    """Probe mixin providing high-level test steps which use yagna market API."""

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def confirm_agreement(self: ProbeProtocol, agreement_id: str) -> None:
        """Call confirm_agreement on the market api."""
        await self.api.market.confirm_agreement(agreement_id)

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def counter_proposal(
        self: ProbeProtocol,
        subscription_id: str,
        demand: Demand,
        provider_proposal: Proposal,
    ) -> str:
        """Call counter_proposal_demand on the market api."""

        proposal = DemandOfferBase(
            constraints=demand.constraints,
            properties=demand.properties,
        )

        counter_proposal = await self.api.market.counter_proposal_demand(
            subscription_id=subscription_id,
            proposal_id=provider_proposal.proposal_id,
            demand_offer_base=proposal,
        )

        return counter_proposal

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def create_agreement(self: ProbeProtocol, proposal: Proposal) -> str:
        """Call create_agreement on the market api."""

        valid_to = str(datetime.utcnow() + timedelta(days=1)) + "Z"
        logger.debug(
            "Creating agreement, proposal_id=%s, valid_to=%s",
            proposal.proposal_id,
            valid_to,
        )
        agreement_proposal = AgreementProposal(proposal_id=proposal.proposal_id, valid_to=valid_to)

        agreement_id = await self.api.market.create_agreement(agreement_proposal)
        return agreement_id

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def subscribe_demand(self: ProbeProtocol, demand: Demand) -> Tuple[str, Demand]:
        """Call subscribe demand on the market api."""
        subscription_id = await self.api.market.subscribe_demand(demand)
        return subscription_id, demand

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def subscribe_template_demand(
        self: ProbeProtocol, task_package: str, constraints: str
    ) -> Tuple[str, Demand]:
        """Build Demand from template and call subscribe demand on market api."""

        demand = DemandOfferBase(
            properties={
                "golem.node.id.name": "test1",
                "golem.srv.comp.expiration": int(
                    (datetime.now() + timedelta(minutes=10)).timestamp() * 1000
                ),
                "golem.srv.comp.task_package": task_package,
                "golem.node.debug.subnet": DEFAULT_SUBNET,
                "golem.com.payment.chosen-platform": self.payment_config.platform_string,
            },
            constraints=constraints,
        )

        return await self.subscribe_demand(demand)  # type: ignore

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def terminate_agreement(self: ProbeProtocol, agreement_id: str, reason: Optional[str]):
        """Call terminate_agreement on the market api."""
        await self.api.market.terminate_agreement(
            agreement_id, request_body={"message": f"Terminated by {self.name}"}
        )

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def unsubscribe_demand(self: ProbeProtocol, subscription_id: str) -> None:
        """Call unsubscribe demand on the market api."""
        await self.api.market.unsubscribe_demand(subscription_id)

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def wait_for_approval(self: ProbeProtocol, agreement_id: str) -> None:
        """Call wait_for_approval on the market api."""
        await self.api.market.wait_for_approval(agreement_id)

    @step(90.0)
    @retry_on(ApiException, 60.0)
    async def wait_for_proposals(
        self: ProbeProtocol,
        subscription_id: str,
        providers: Sequence["Probe"],
        filter: Optional[Callable[[Proposal], bool]] = lambda p: True,
    ) -> List[Proposal]:
        """Call collect_offers on the market api.

        Polls collect_offers continously until an offer from each of the given
        providers is received. Returns a list of the collected proposals.
        """
        proposals: List[Proposal] = []
        provider_ids = {p.address for p in providers}

        while len(proposals) < len(provider_ids):
            collected_offers = await self.api.market.collect_offers(subscription_id, timeout=1)
            if collected_offers:
                logger.debug(
                    "collect_offers(%s). collected_offers=%r",
                    subscription_id,
                    collected_offers,
                )
                collected_proposals = [
                    offer.proposal
                    for offer in collected_offers
                    if (offer.proposal.issuer_id in provider_ids and filter(offer.proposal))
                ]
                proposals.extend(collected_proposals)
            else:
                logger.debug("Waiting for proposals. subscription_id=%s", subscription_id)

        return proposals


class PaymentApiMixin:
    """Probe mixin providing high-level test steps which use yagna payment API."""

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def gather_invoices(self: ProbeProtocol, agreement_id: str) -> List[Invoice]:
        """Call gather_invoice on the payment api."""

        invoices: List[Invoice] = []

        while not invoices:
            await asyncio.sleep(2.0)
            invoices = await self.api.payment.get_invoices()
            invoices = [inv for inv in invoices if inv.agreement_id == agreement_id]

        return invoices

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def pay_invoices(self: ProbeProtocol, invoice_events: Iterable[Invoice]) -> None:
        """Call accept_invoice on the payment api."""

        for invoice_event in invoice_events:
            allocation = Allocation(
                allocation_id="",
                total_amount=invoice_event.amount,
                spent_amount=0,
                remaining_amount=0,
                make_deposit=True,
                timestamp=datetime.now(timezone.utc),
                payment_platform=self.payment_config.platform_string,
                deposit=None,
            )

            allocation_result = await self._create_allocation(allocation)

            acceptance = Acceptance(
                total_amount_accepted=invoice_event.amount,
                allocation_id=allocation_result.allocation_id,
            )
            await self.api.payment.accept_invoice(invoice_event.invoice_id, acceptance)
            logger.debug("Accepted invoice. id=%s", invoice_event.invoice_id)

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def create_allocation(
        self: ProbeProtocol, timeout: Optional[datetime] = None, total_amount=0
    ) -> Allocation:
        """Call create_allocation on the market api."""

        allocation = Allocation(
            allocation_id="",
            total_amount=total_amount,
            spent_amount=0,
            remaining_amount=0,
            make_deposit=True,
            timestamp=datetime.now(timezone.utc),
            timeout=timeout,
            payment_platform=self.payment_config.platform_string,
            deposit=None,
        )

        allocation_result = await self._create_allocation(allocation)

        return allocation_result

    @step(70.0)
    @retry_on(ApiException, 60.0)
    async def get_allocation(self: ProbeProtocol, allocation_id: str) -> Allocation:
        """Call get_allocation on the market api."""

        allocation_result = await self.api.payment.get_allocation(allocation_id)

        return allocation_result

    async def _create_allocation(self: ProbeProtocol, allocation: Allocation) -> Allocation:
        allocation_result = await self.api.payment.create_allocation(allocation)
        logger.debug("Created allocation. id=%s", allocation_result.allocation_id)

        return allocation_result
