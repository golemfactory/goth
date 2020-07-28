"""Helpers to build sequence on the runner attached to different probes."""

from asyncio import Future
from datetime import datetime, timedelta
import logging
import json
import os
from pathlib import Path
import re
import time
from typing import Dict, Iterable, List, Set, Tuple

from goth.assertions import EventStream
from goth.runner.log_monitor import LogEvent
from goth.runner.probe import Probe
from goth.runner.provider import ProviderProbe
from goth.runner.sequence.step import AssertionStep, CallableStep, Step

from openapi_market_client import Demand, Proposal, AgreementProposal
from openapi_activity_client import ExeScriptRequest, ExeScriptCommandResult
from openapi_payment_client import Allocation, Acceptance, InvoiceEvent

logger = logging.getLogger(__name__)

LogEvents = EventStream[LogEvent]


class ProbeStepBuilder:
    """Helper for creating test sequence to be ran inside the runner."""

    def __init__(self, steps, probes: List[Probe]):
        self._steps: List[Step] = steps
        self._probes = probes

        # Requestor only
        # FIXME: exe_script should be an argument to `call_exec`
        my_path = os.path.abspath(os.path.dirname(__file__))
        exe_script_file = Path(my_path + "/../../../test/level0/asset/exe_script.json")
        self.exe_script_txt = exe_script_file.read_text()
        logger.debug("exe_script read. contents=%s", self.exe_script_txt)

    @property
    def probes(self) -> List[Probe]:
        """Return the list of probes on which this builder operates."""
        return self._probes

    def log(self, fut: Future):
        """Log the contents of the future."""

        def _call_log(probe: Probe):
            contents = fut.result()
            logger.debug("probe=%s, contents=%r", probe, contents)

        step = CallableStep(
            name="log", timeout=10, probes=self._probes, callback=_call_log
        )
        self._steps.append(step)

    # --- PROVIDER --- #

    def wait_for_offer_subscribed(self):
        """Wait until the provider agent subscribes to the offer."""
        self._wait_for_log("wait_for_offer_subscribed", "Subscribed offer")

    def wait_for_proposal_accepted(self):
        """Wait until the provider agent accepts the proposal."""
        self._wait_for_log("wait_for_proposal_accepted", "Decided to AcceptProposal")

    def wait_for_agreement_approved(self):
        """Wait until the provider agent accepts the agreement."""
        self._wait_for_log("wait_for_agreement_approved", "Decided to ApproveAgreement")

    def wait_for_activity_created(self):
        """Wait until the provider agent receives the activity."""
        self._wait_for_log("wait_for_activity_created", "Activity created")

    def wait_for_exeunit_started(self):
        """Wait until the provider agent starts the exe-unit."""
        self._wait_for_log("wait_for_exeunit_started", r"\[ExeUnit\](.+)Started$")

    def wait_for_exeunit_finished(self):
        """Wait until exe-unit finishes."""
        self._wait_for_log(
            "wait_for_exeunit_finished",
            "ExeUnit process exited with status Finished - exit code: 0",
        )

    def wait_for_invoice_sent(self):
        """Wait until the invoice is sent."""
        self._wait_for_log("wait_for_invoice_sent", r"Invoice (.+) sent")

    def wait_for_invoice_paid(self):
        """Wait until the invoice is paid."""
        self._wait_for_log(
            "wait_for_invoice_paid",
            "Invoice .+? for agreement .+? was paid",
            timeout=30,
        )

    def _wait_for_log(self, name: str, pattern: str, timeout: int = 20):
        step = AssertionStep(name, timeout)
        for probe in self._probes:
            assertion = assert_message_starts_with(pattern)
            result = probe.agent_logs.add_assertion(assertion)
            result.name = f"assert_message_starts_with({pattern})"
            step.add_assertion(result)
        self._steps.append(step)

    # --- REQUESTOR --- #

    def init_payment(self):
        """Call init_payment on the requestor CLI."""

        def _call_init_payment(probe: Probe):
            result = probe.cli.payment_init(requestor_mode=True)
            return result

        step = CallableStep(
            name="init_payment",
            timeout=120,
            probes=self._probes,
            callback=_call_init_payment,
        )
        self._steps.append(step)

    def subscribe_demand(self) -> "Future[Tuple[str, Demand]]":
        """Call subscribe demand on the requestor market api."""

        awaitable = Future()

        package = (
            "hash://sha3:d5e31b2eed628572a5898bf8c34447644bfc4b5130cfc1e4f10aeaa1"
            ":http://3.249.139.167:8000/rust-wasi-tutorial.zip"
        )
        constraints = (
            "(&(golem.inf.mem.gib>0.5)(golem.inf.storage.gib>1)"
            "(golem.com.pricing.model=linear))"
        )

        def _call_subscribe_demand(probe: Probe) -> Tuple[str, Demand]:
            demand = Demand(
                requestor_id=probe.address,
                properties={
                    "golem.node.id.name": "test1",
                    "golem.srv.comp.expiration": int(
                        (datetime.now() + timedelta(days=1)).timestamp() * 1000
                    ),
                    "golem.srv.comp.task_package": package,
                },
                constraints=constraints,
            )

            subscription_id = probe.market.subscribe_demand(demand)

            awaitable.set_result((subscription_id, demand))
            return (subscription_id, demand)

        step = CallableStep(
            name="subscribe_demand",
            timeout=10,
            probes=self._probes,
            callback=_call_subscribe_demand,
        )
        self._steps.append(step)
        return awaitable

    def unsubscribe_demand(
        self, fut_subscription_id: "Future[Tuple[str, Demand]]"
    ) -> Future:
        """Call unsubscribe demand on the requestor market api."""

        awaitable = Future()

        def _call_unsubscribe_demand(probe: Probe):
            subscription_id, demand = fut_subscription_id.result()

            result = probe.market.unsubscribe_demand(subscription_id)

            awaitable.set_result(result)
            return result

        step = CallableStep(
            name="unsubscribe_demand",
            timeout=10,
            probes=self._probes,
            callback=_call_unsubscribe_demand,
        )
        self._steps.append(step)
        return awaitable

    def wait_for_proposals(
        self,
        fut_subscription_id: "Future[Tuple[str, Demand]]",
        providers: List[Probe],
    ) -> "Future[List[Proposal]]":
        """Call collect_offers on the requestor market api.

        Return one offer for each of the given provider nodes.
        """

        awaitable = Future()

        def _call_wait_for_proposals(probe: Probe) -> List[Proposal]:
            subscription_id, _ = fut_subscription_id.result()
            provider_ids = {p.address for p in providers}
            proposals: Dict[str, Proposal] = {}

            while len(proposals) < len(provider_ids):
                collected_offers = probe.market.collect_offers(subscription_id)
                if collected_offers:
                    logger.debug(
                        "collect_offers(%s). collected_offers=%r",
                        subscription_id,
                        collected_offers,
                    )
                    collected_proposals = [
                        offer.proposal
                        for offer in collected_offers
                        if offer.proposal.issuer_id in provider_ids
                    ]
                    for proposal in collected_proposals:
                        proposals[proposal.issuer_id] = proposal
                else:
                    logger.debug(
                        "Waiting for proposals. subscription_id=%s", subscription_id
                    )
                    time.sleep(1.0)

            result = proposals.values()
            awaitable.set_result(result)
            return result

        step = CallableStep(
            name="wait_for_proposals",
            timeout=len(providers) * 10,
            probes=self._probes,
            callback=_call_wait_for_proposals,
        )
        self._steps.append(step)
        return awaitable

    def counter_proposals(
        self,
        fut_subscription_id: "Future[Tuple[str, Demand]]",
        fut_proposals: "Future[List[Proposal]]",
    ) -> "Future[List[Proposal]]":
        """Call counter_proposal_demand on the requestor market api.

        Return a list of counter proposals created.
        """

        awaitable = Future()

        def _call_counter_proposals(probe: Probe) -> Proposal:
            subscription_id, demand = fut_subscription_id.result()
            counter_proposals: List[Proposal] = []
            for provider_proposal in fut_proposals.result():
                proposal = Proposal(
                    constraints=demand.constraints,
                    properties=demand.properties,
                    prev_proposal_id=provider_proposal.proposal_id,
                )
                counter_proposal = probe.market.counter_proposal_demand(
                    subscription_id=subscription_id,
                    proposal_id=provider_proposal.proposal_id,
                    proposal=proposal,
                )
                counter_proposals.append(counter_proposal)

            awaitable.set_result(counter_proposals)
            return counter_proposals

        step = CallableStep(
            name="counter_proposals",
            timeout=10,
            probes=self._probes,
            callback=_call_counter_proposals,
        )
        self._steps.append(step)
        return awaitable

    def create_agreements(
        self, fut_proposals: "Future[List[Proposal]]"
    ) -> "Future[List[str]]":
        """Call create_agreement on the requestor market api.

        Return a list of agreement IDs created during this step.
        """

        awaitable = Future()

        def _call_create_agreements(probe: Probe) -> str:
            agreement_ids: List[str] = []
            for proposal in fut_proposals.result():
                valid_to = str(datetime.utcnow() + timedelta(days=1)) + "Z"
                logger.debug(
                    "Creating agreement, proposal_id=%s, valid_to=%s",
                    proposal.proposal_id,
                    valid_to,
                )
                agreement_proposal = AgreementProposal(
                    proposal_id=proposal.proposal_id, valid_to=valid_to
                )

                agreement_id = probe.market.create_agreement(agreement_proposal)
                agreement_ids.append(agreement_id)

            awaitable.set_result(agreement_ids)
            return agreement_ids

        step = CallableStep(
            name="create_agreements",
            timeout=10,
            probes=self._probes,
            callback=_call_create_agreements,
        )
        self._steps.append(step)
        return awaitable

    def confirm_agreements(self, fut_agreement_ids: "Future[List[str]]") -> Future:
        """Call confirm_agreement on the requestor market api."""

        awaitable = Future()

        def _call_confirm_agreement(probe: Probe):
            for agreement_id in fut_agreement_ids.result():
                probe.market.confirm_agreement(agreement_id)

            awaitable.set_result(None)
            return None

        step = CallableStep(
            name="confirm_agreements",
            timeout=10,
            probes=self._probes,
            callback=_call_confirm_agreement,
        )
        self._steps.append(step)
        return awaitable

    def create_activities(
        self, fut_agreement_ids: "Future[List[str]]"
    ) -> "Future[List[str]]":
        """Call create_activity on the requestor activity api.

        Return a list of activity IDs created during this step.
        """

        awaitable = Future()

        def _call_create_activities(probe: Probe) -> List[str]:
            activity_ids: List[str] = []

            for agreement_id in fut_agreement_ids.result():
                activity_id = probe.activity.control.create_activity(agreement_id)
                activity_ids.append(activity_id)

            awaitable.set_result(activity_ids)
            return activity_ids

        step = CallableStep(
            name="create_activities",
            timeout=10,
            probes=self._probes,
            callback=_call_create_activities,
        )
        self._steps.append(step)
        return awaitable

    def call_exec(
        self, fut_activity_ids: "Future[List[str]]"
    ) -> "Future[List[Tuple[str, str]]]":
        """Call call_exec on the requestor activity api.

        Return a list of tuples, each consisting of an activity ID and its
        corresponding batch ID. Batch IDs are results of the `call_exec` invocations.
        """

        awaitable = Future()

        def _call_call_exec(probe: Probe) -> str:
            activity_batch_ids: List[Tuple[str, str]] = []
            for activity_id in fut_activity_ids.result():
                batch_id = probe.activity.control.call_exec(
                    activity_id, ExeScriptRequest(self.exe_script_txt)
                )
                activity_batch_ids.append((activity_id, batch_id))

            awaitable.set_result(activity_batch_ids)
            return activity_batch_ids

        step = CallableStep(
            name="call_exec", timeout=10, probes=self._probes, callback=_call_call_exec
        )
        self._steps.append(step)
        return awaitable

    def collect_results(
        self, fut_activity_batches: "Future[List[Tuple[str, str]]]"
    ) -> "Future[List[List[ExeScriptCommandResult]]]":
        """Call collect_results on the requestor activity api.

        Return a list of exe script results, each item being a list of
        `ExeScriptCommandResult` objects.
        """

        awaitable = Future()

        def _call_collect_results(probe: Probe) -> List[ExeScriptCommandResult]:
            exe_script_results: List[List[ExeScriptCommandResult]] = []
            for (activity_id, batch_id) in fut_activity_batches.result():
                commands_cnt = len(json.loads(self.exe_script_txt))
                results = probe.activity.control.get_exec_batch_results(
                    activity_id, batch_id
                )
                while len(results) < commands_cnt:
                    time.sleep(1.0)
                    results = probe.activity.control.get_exec_batch_results(
                        activity_id, batch_id
                    )
                exe_script_results.append(results)

            awaitable.set_result(exe_script_results)
            return exe_script_results

        step = CallableStep(
            name="collect_results",
            timeout=10,
            probes=self._probes,
            callback=_call_collect_results,
        )
        self._steps.append(step)
        return awaitable

    def destroy_activities(self, fut_activity_ids: "Future[List[str]]") -> Future:
        """Call destroy_activity on the requestor activity api."""

        awaitable = Future()

        def _call_destroy_activities(probe: Probe):
            for activity_id in fut_activity_ids.result():
                probe.activity.control.destroy_activity(activity_id)

            awaitable.set_result(None)
            return None

        step = CallableStep(
            name="destroy_activities",
            timeout=10,
            probes=self._probes,
            callback=_call_destroy_activities,
        )
        self._steps.append(step)
        return awaitable

    def gather_invoices(
        self, fut_agreement_ids: "Future[List[str]]"
    ) -> "Future[Set[InvoiceEvent]]":
        """Call gather_invoice on the requestor payment api.

        Return a set of invoice events corresponding to the agreement IDs passed as an
        argument to this step.
        """

        awaitable = Future()

        def _call_gather_invoices(probe: Probe) -> InvoiceEvent:
            agreement_ids = fut_agreement_ids.result()

            invoice_events: Dict[str, InvoiceEvent] = {}
            while len(invoice_events) < len(agreement_ids):
                time.sleep(2.0)
                events = probe.payment.get_received_invoices()
                logger.debug(f"Gathered invoice_event {events}")
                filtered_events = list(
                    filter(lambda x: x.agreement_id in agreement_ids, events)
                )
                logger.debug(f"filtered invoice_event {filtered_events}")
                for event in filtered_events:
                    invoice_events[event.invoice_id] = event
                logger.debug("invoice_events: %s", invoice_events)

            result = invoice_events.values()
            awaitable.set_result(result)
            return result

        step = CallableStep(
            name="gather_invoices",
            timeout=10,
            probes=self._probes,
            callback=_call_gather_invoices,
        )
        self._steps.append(step)
        return awaitable

    def pay_invoices(
        self, fut_invoice_events: "Future[Iterable[InvoiceEvent]]"
    ) -> Future:
        """Call accept_invoice on the requestor payment api."""

        awaitable = Future()

        def _call_pay_invoices(probe: Probe):
            for invoice_event in fut_invoice_events.result():
                allocation = Allocation(
                    total_amount=invoice_event.amount,
                    spent_amount=0,
                    remaining_amount=0,
                    make_deposit=True,
                )
                allocation_result = probe.payment.create_allocation(allocation)
                logger.debug(f"Created allocation. id={allocation_result}")

                acceptance = Acceptance(
                    total_amount_accepted=invoice_event.amount,
                    allocation_id=allocation_result.allocation_id,
                )
                probe.payment.accept_invoice(invoice_event.invoice_id, acceptance)
                logger.debug(f"Accepted invoice. id={invoice_event.invoice_id}")

            awaitable.set_result(None)
            return None

        step = CallableStep(
            name="pay_invoices",
            timeout=10,
            probes=self._probes,
            callback=_call_pay_invoices,
        )
        self._steps.append(step)
        return awaitable


# --- ASSERTIONS --- #
# TODO: Move to own file


def assert_message_starts_with(needle: str):
    """Return the "message.start_with" assertion with pre-compiled re `needle`.

    Prepare an assertion that:
    Assert that a `LogEvent` with message starts with {needle} is found.
    """

    # No need to add ^ in the regexp since .match( searches from the start
    pattern = re.compile(needle)

    async def _assert_starts_with(stream: LogEvents):

        async for event in stream:
            match = pattern.match(event.message)
            if match:
                return True

        raise AssertionError(f"No message starts with '{needle}'")

    return _assert_starts_with
