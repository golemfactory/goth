"""Probe mixins containing high-level steps."""

import asyncio
from datetime import datetime, timedelta
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

from ya_activity import ExeScriptCommandResult, ExeScriptRequest
from ya_market import AgreementProposal, Demand, DemandOfferBase, Proposal
from ya_payment import Acceptance, Allocation, Invoice

from goth.node import DEFAULT_SUBNET
from goth.runner.step import step

if TYPE_CHECKING:
    from goth.runner.probe import Probe
    from goth.runner.probe.rest_client import RestApiComponent

logger = logging.getLogger(__name__)


class ProbeProtocol(Protocol):
    """Protocol class representing the probe interface in mixins.

    This is mainly to fix mypy errors when using `Probe` directly as `self` type.
    """

    api: "RestApiComponent"
    """REST API probe component."""


class RequestorApiMixin:
    """Provides high-level steps that rely on Yagna Activity API."""

    @step()
    async def create_activity(self: ProbeProtocol, agreement_id: str) -> str:
        """Call create_activity on the requestor activity api."""

        activity_id = await self.api.activity.control.create_activity(agreement_id)
        return activity_id

    @step()
    async def call_exec(self: ProbeProtocol, activity_id: str, exe_script: str) -> str:
        """Call call_exec on the requestor activity api."""

        script_request = ExeScriptRequest(exe_script)
        batch_id = await self.api.activity.control.call_exec(
            activity_id, script_request
        )
        return batch_id

    @step()
    async def collect_results(
        self: ProbeProtocol, activity_id: str, batch_id: str, num_results: int
    ) -> List[ExeScriptCommandResult]:
        """Call collect_results on the requestor activity api."""

        results: List[ExeScriptCommandResult] = []

        while len(results) < num_results:
            results = await self.api.activity.control.get_exec_batch_results(
                activity_id, batch_id
            )
            await asyncio.sleep(1.0)
        return results

    @step()
    async def destroy_activity(self: ProbeProtocol, activity_id: str) -> None:
        """Call destroy_activity on the requestor activity api."""

        await self.api.activity.control.destroy_activity(activity_id)

    @step()
    async def subscribe_demand(
        self: ProbeProtocol, demand: Demand
    ) -> Tuple[str, Demand]:
        """Call subscribe demand on the requestor market api."""
        subscription_id = await self.api.market.subscribe_demand(demand)
        return subscription_id, demand

    @step()
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
            },
            constraints=constraints,
        )

        return await self.subscribe_demand(demand)  # type: ignore

    @step()
    async def unsubscribe_demand(self: ProbeProtocol, subscription_id: str) -> None:
        """Call unsubscribe demand on the requestor market api."""
        await self.api.market.unsubscribe_demand(subscription_id)

    @step()
    async def wait_for_proposals(
        self: ProbeProtocol,
        subscription_id: str,
        providers: Sequence["Probe"],
        filter: Optional[Callable[[Proposal], bool]] = lambda p: True,
    ) -> List[Proposal]:
        """Call collect_offers on the requestor market api.

        Polls collect_offers continously until an offer from each of the given
        providers is received. Returns a list of the collected proposals.
        """
        proposals: List[Proposal] = []
        provider_ids = {p.address for p in providers}

        while len(proposals) < len(provider_ids):
            collected_offers = await self.api.market.collect_offers(subscription_id)
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

        return proposals

    @step()
    async def counter_proposal(
        self: ProbeProtocol,
        subscription_id: str,
        demand: Demand,
        provider_proposal: Proposal,
    ) -> str:
        """Call counter_proposal_demand on the requestor market api."""

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

    @step()
    async def create_agreement(self: ProbeProtocol, proposal: Proposal) -> str:
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

        agreement_id = await self.api.market.create_agreement(agreement_proposal)
        return agreement_id

    @step()
    async def confirm_agreement(self: ProbeProtocol, agreement_id: str) -> None:
        """Call confirm_agreement on the requestor market api."""
        await self.api.market.confirm_agreement(agreement_id)

    @step()
    async def wait_for_approval(self: ProbeProtocol, agreement_id: str) -> None:
        """Call wait_for_approval on the requestor market api."""
        await self.api.market.wait_for_approval(agreement_id)

    @step()
    async def terminate_agreement(
        self: ProbeProtocol, agreement_id: str, reason: Optional[str]
    ):
        """Call terminate_agreement on the requestor market api."""
        await self.api.market.terminate_agreement(
            agreement_id, request_body={"message": "Terminated by requestor"}
        )

    @step()
    async def gather_invoices(self: ProbeProtocol, agreement_id: str) -> List[Invoice]:
        """Call gather_invoice on the requestor payment api."""

        invoices: List[Invoice] = []

        while not invoices:
            await asyncio.sleep(2.0)
            invoices = await self.api.payment.get_invoices()
            invoices = [inv for inv in invoices if inv.agreement_id == agreement_id]

        return invoices

    @step()
    async def pay_invoices(
        self: ProbeProtocol, invoice_events: Iterable[Invoice]
    ) -> None:
        """Call accept_invoice on the requestor payment api."""

        for invoice_event in invoice_events:
            allocation = Allocation(
                allocation_id="",
                total_amount=invoice_event.amount,
                spent_amount=0,
                remaining_amount=0,
                make_deposit=True,
            )
            allocation_result = await self.api.payment.create_allocation(allocation)
            logger.debug("Created allocation. id=%s", allocation_result)

            acceptance = Acceptance(
                total_amount_accepted=invoice_event.amount,
                allocation_id=allocation_result.allocation_id,
            )
            await self.api.payment.accept_invoice(invoice_event.invoice_id, acceptance)
            logger.debug("Accepted invoice. id=%s", invoice_event.invoice_id)


class ProviderLogMixin:
    """A provider probe with steps that wait for specific messages in agent logs."""

    @step()
    async def wait_for_offer_subscribed(self):
        """Wait until the provider agent subscribes to the offer."""
        await self._wait_for_agent_log("Subscribed offer")

    @step()
    async def wait_for_proposal_accepted(self):
        """Wait until the provider agent subscribes to the offer."""
        await self._wait_for_agent_log("Decided to CounterProposal")

    @step()
    async def wait_for_agreement_approved(self):
        """Wait until the provider agent subscribes to the offer."""
        await self._wait_for_agent_log("Decided to ApproveAgreement")

    @step()
    async def wait_for_exeunit_started(self):
        """Wait until the provider agent starts the exe-unit."""
        await self._wait_for_agent_log(r"(.*)\[ExeUnit\](.+)Supervisor initialized$")

    @step()
    async def wait_for_exeunit_finished(self):
        """Wait until exe-unit finishes."""
        await self._wait_for_agent_log(
            "ExeUnit process exited with status Finished - exit code: 0"
        )

    @step()
    async def wait_for_agreement_terminated(self):
        """Wait until Agreement will be terminated.

        This can happen for 2 reasons (both caught by this function):
        - Requestor terminates - most common case
        - Provider terminates - it happens for compatibility with previous
        versions of API without `terminate` endpoint implemented. Moreover
        Provider can terminate, because Agreements condition where broken.
        """
        await self._wait_for_agent_log(r"Agreement \[.*\] terminated by")

    @step()
    async def wait_for_agreement_cleanup(self):
        """Wait until Provider will cleanup all allocated resources.

        This can happen before or after Agreement terminated log will be printed.
        """
        await self._wait_for_agent_log(r"Agreement \[.*\] cleanup finished.")

    @step()
    async def wait_for_invoice_sent(self):
        """Wait until the invoice is sent."""
        await self._wait_for_agent_log("Invoice (.+) sent")

    @step(default_timeout=300)
    async def wait_for_invoice_paid(self):
        """Wait until the invoice is paid."""
        await self._wait_for_agent_log("Invoice .+? for agreement .+? was paid")
