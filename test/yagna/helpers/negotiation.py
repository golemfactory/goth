"""Helper functions for building custom Offers and negotiating Agreements."""

import logging
from typing import List, Optional, Callable, Tuple, Any
from datetime import datetime, timedelta

from ya_market import Demand, DemandOfferBase, Proposal

from goth.node import DEFAULT_SUBNET
from goth.runner.probe import ProviderProbe, RequestorProbe


logger = logging.getLogger(__name__)


class DemandBuilder:
    """Helper for building custom Demands.

    Use if RequestorProbe.subscribe_template_demand function
    is not enough for you.
    """

    def __init__(self, requestor: RequestorProbe):
        self._requestor = requestor
        self._properties = dict()
        self._constraints = "()"
        self._properties["golem.node.debug.subnet"] = DEFAULT_SUBNET

    def props_from_template(self, task_package: str) -> "DemandBuilder":
        """Build default properties."""

        new_props = {
            "golem.node.id.name": f"test-requestor-{self._requestor.name}",
            "golem.srv.comp.expiration": int(
                (datetime.now() + timedelta(minutes=10)).timestamp() * 1000
            ),
            "golem.srv.comp.task_package": task_package,
        }
        self._properties.update(new_props)
        return self

    def property(self, key: str, value: Any) -> "DemandBuilder":
        """Add property."""
        self._properties[key] = value
        return self

    # TODO: Building constraints.
    def constraints(self, constraints: str) -> "DemandBuilder":
        """Add constraints.

        Note: This will override previous constraints.
        """

        self._constraints = constraints
        return self

    def build(self) -> DemandOfferBase:
        """Create Demand from supplied parameters."""
        return DemandOfferBase(
            properties=self._properties,
            constraints=self._constraints,
        )


async def negotiate_agreements(
    requestor: RequestorProbe,
    demand: Demand,
    providers: List[ProviderProbe],
    proposal_filter: Optional[Callable[[Proposal], bool]] = lambda p: True,
) -> List[Tuple[str, ProviderProbe]]:
    """Negotiate agreements with supplied providers.

    Use negotiate_agreements function, when you don't need any custom negotiation
    logic, but rather you want to test further parts of yagna protocol
    and need ready Agreements.
    """
    for provider in providers:
        await provider.wait_for_offer_subscribed()

    subscription_id, demand = await requestor.subscribe_demand(demand)

    proposals = await requestor.wait_for_proposals(
        subscription_id,
        providers,
        proposal_filter,
    )
    logger.info("Collected %s proposals", len(proposals))

    agreement_providers = []

    for proposal in proposals:
        provider = next(p for p in providers if p.address == proposal.issuer_id)
        logger.info("Processing proposal from %s", provider.name)

        counter_proposal_id = await requestor.counter_proposal(
            subscription_id, demand, proposal
        )
        await provider.wait_for_proposal_accepted()

        new_proposals = await requestor.wait_for_proposals(
            subscription_id,
            (provider,),
            lambda proposal: proposal.prev_proposal_id == counter_proposal_id,
        )

        agreement_id = await requestor.create_agreement(new_proposals[0])
        await requestor.confirm_agreement(agreement_id)
        await provider.wait_for_agreement_approved()
        await requestor.wait_for_approval(agreement_id)
        agreement_providers.append((agreement_id, provider))

    await requestor.unsubscribe_demand(subscription_id)
    logger.info("Got %s agreements", len(agreement_providers))

    return agreement_providers
