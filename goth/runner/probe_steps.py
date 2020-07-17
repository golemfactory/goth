"""Helpers to build steps on the runner attached to different probes."""

import abc
from asyncio import Future, sleep
from datetime import datetime, timedelta
import logging
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Callable, List, Tuple

from goth.assertions import EventStream, Assertion
from goth.runner.log_monitor import LogEvent
from goth.runner.probe import Probe

from openapi_market_client import Demand, Proposal, AgreementProposal
from openapi_activity_client import ExeScriptRequest, ExeScriptCommandResult
from openapi_payment_client import Allocation, Acceptance, InvoiceEvent

logger = logging.getLogger(__name__)

LogEvents = EventStream[LogEvent]


class Step(abc.ABC):
    """Step to be awaited in the runner."""

    def __init__(self, name: str, timeout: int):
        self.name = name
        self.timeout = timeout

    @abc.abstractmethod
    async def tick(self):
        """Wait untill this step is complete.

        Implemented in sub-classes of Step
        """

    def __str__(self):
        return f"{self.name}(timeout={self.timeout})"

    def __repr__(self):
        return f"<{type(self).__name__} name={self.name} timeout={self.timeout}>"


class AssertionStep(Step):
    """Step that holds a set of assertions to await."""

    assertions: List[Assertion]
    """All assertions that have to pass for this step."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assertions = []

    def add_assertion(self, assertion: Assertion):
        """Add an assertion to be awaited in this step."""
        self.assertions.append(assertion)

    async def tick(self) -> bool:
        """Handle required action and return `True` iff this step has been completed.

        For the AssertionStep this means all assertions are marked as done.
        """
        while not all(a.done for a in self.assertions):
            await sleep(0.1)


class CallableStep(Step):
    """Step that executes a python function call on all `probes`."""

    probes: List[Probe]
    """Probes to execute `callable(probe)` for."""
    callback: Callable[[Probe], Any]
    """Callable to be executed for each probe when the step is ticked"""

    def __init__(
        self,
        name: str,
        timeout: int,
        probes: List[Probe],
        callback: Callable[[Probe], Any],
    ):
        super().__init__(name, timeout)
        self.probes = probes
        self.callback = callback

    async def tick(self) -> bool:
        """Handle required action and return `True` iff this step has been completed.

        For the CallableStep this means the callback is executed for each probe.
        """
        for probe in self.probes:
            res = self.callback(probe)
            logger.debug("step=%s, probe=%s result=%r", self, probe, res)
            if not probe == self.probes[-1]:
                # Sleep to allow other asyncio Tasks to continue
                await sleep(0.1)
        return True


class ProbeStepBuilder:
    """Helper for creating test steps to be ran inside the runner."""

    def __init__(self, steps, probes: List[Probe]):
        self._steps: List[Step] = steps
        self._probes = probes

        # Requestor only
        my_path = os.path.abspath(os.path.dirname(__file__))
        exe_script_file = Path(my_path + "/../../test/level0/asset/exe_script.json")
        self.exe_script_txt = exe_script_file.read_text()
        logger.debug("exe_script read. contents=%s", self.exe_script_txt)

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
            timeout=60 * 5,
        )

    def _wait_for_log(self, name: str, pattern: str, timeout: int = 10):
        step = AssertionStep(name, timeout)
        for probe in self._probes:
            assertion = assert_message_starts_with(pattern)
            result = probe.agent_logs.add_assertion(assertion)
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
            ":http://34.244.4.185:8000/rust-wasi-tutorial.zip"
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

    def wait_for_proposal(
        self, fut_subscription_id: "Future[Tuple[str, Demand]]"
    ) -> "Future[Proposal]":
        """Call collect_offers on the requestor market api.

        Return the first proposal.
        """

        awaitable = Future()

        def _call_wait_for_proposal(probe: Probe) -> Proposal:
            subscription_id, _ = fut_subscription_id.result()
            proposal = None

            while proposal is None:
                result_offers = probe.market.collect_offers(subscription_id)
                logger.debug(
                    "collect_offers(%s). proposal=%r", subscription_id, result_offers,
                )
                if result_offers:
                    proposal = result_offers[0].proposal
                else:
                    logger.debug("Waiting on proposal... %r", result_offers)
                    time.sleep(1.0)

            awaitable.set_result(proposal)
            return proposal

        step = CallableStep(
            name="wait_for_proposal",
            timeout=10,
            probes=self._probes,
            callback=_call_wait_for_proposal,
        )
        self._steps.append(step)
        return awaitable

    def counter_proposal(
        self,
        fut_subscription_id: "Future[Tuple[str, Demand]]",
        fut_proposal: "Future[Proposal]",
    ) -> "Future[Proposal]":
        """Call counter_proposal_demand on the requestor market api."""

        awaitable = Future()

        def _call_counter_proposal(probe: Probe) -> Proposal:
            subscription_id, demand = fut_subscription_id.result()
            provider_proposal = fut_proposal.result()
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

            awaitable.set_result(counter_proposal)
            return counter_proposal

        step = CallableStep(
            name="counter_proposal",
            timeout=10,
            probes=self._probes,
            callback=_call_counter_proposal,
        )
        self._steps.append(step)
        return awaitable

    def create_agreement(self, fut_proposal: "Future[Proposal]") -> "Future[str]":
        """Call create_agreement on the requestor market api."""

        awaitable = Future()

        def _call_create_agreement(probe: Probe) -> str:
            proposal = fut_proposal.result()
            valid_to = str(datetime.utcnow() + timedelta(days=1)) + "Z"
            logger.debug(
                "Creatiing agreement, proposal_id=%s, valid_to=%s",
                proposal.proposal_id,
                valid_to,
            )
            agreement_proposal = AgreementProposal(
                proposal_id=proposal.proposal_id, valid_to=valid_to
            )

            agreement_id = probe.market.create_agreement(agreement_proposal)

            awaitable.set_result(agreement_id)
            return agreement_id

        step = CallableStep(
            name="create_agreement",
            timeout=10,
            probes=self._probes,
            callback=_call_create_agreement,
        )
        self._steps.append(step)
        return awaitable

    def confirm_agreement(self, fut_agreement_id: "Future[str]") -> Future:
        """Call confirm_agreement on the requestor market api."""

        awaitable = Future()

        def _call_confirm_agreement(probe: Probe):
            agreement_id = fut_agreement_id.result()

            result = probe.market.confirm_agreement(agreement_id)

            awaitable.set_result(result)
            return result

        step = CallableStep(
            name="confirm_agreement",
            timeout=10,
            probes=self._probes,
            callback=_call_confirm_agreement,
        )
        self._steps.append(step)
        return awaitable

    def create_activity(self, fut_agreement_id: "Future[str]") -> "Future[str]":
        """Call create_activity on the requestor activity api."""

        awaitable = Future()

        def _call_create_activity(probe: Probe) -> str:
            agreement_id = fut_agreement_id.result()

            activity_id = probe.activity.control.create_activity(agreement_id)

            awaitable.set_result(activity_id)
            return activity_id

        step = CallableStep(
            name="create_activity",
            timeout=10,
            probes=self._probes,
            callback=_call_create_activity,
        )
        self._steps.append(step)
        return awaitable

    def call_exec(self, fut_activity_id: "Future[str]") -> "Future[str]":
        """Call call_exec on the requestor activity api."""

        awaitable = Future()

        def _call_call_exec(probe: Probe) -> str:
            activity_id = fut_activity_id.result()

            batch_id = probe.activity.control.call_exec(
                activity_id, ExeScriptRequest(self.exe_script_txt)
            )

            awaitable.set_result(batch_id)
            return batch_id

        step = CallableStep(
            name="call_exec", timeout=10, probes=self._probes, callback=_call_call_exec
        )
        self._steps.append(step)
        return awaitable

    def collect_results(
        self, fut_activity_id: "Future[str]", fut_batch_id: "Future[str]"
    ) -> "Future[List[ExeScriptCommandResult]]":
        """Call collect_results on the requestor activity api."""

        awaitable = Future()

        def _call_collect_results(probe: Probe) -> List[ExeScriptCommandResult]:
            activity_id = fut_activity_id.result()
            batch_id = fut_batch_id.result()

            commands_cnt = len(json.loads(self.exe_script_txt))
            # probe.activity.state.get_activity_state(activity_id)
            results = probe.activity.control.get_exec_batch_results(
                activity_id, batch_id
            )
            while len(results) < commands_cnt:
                time.sleep(1.0)
                # probe.activity.state.get_activity_state(activity_id)
                results = probe.activity.control.get_exec_batch_results(
                    activity_id, batch_id
                )

            awaitable.set_result(results)
            return results

        step = CallableStep(
            name="collect_results",
            timeout=10,
            probes=self._probes,
            callback=_call_collect_results,
        )
        self._steps.append(step)
        return awaitable

    def destroy_activity(self, fut_activity_id: "Future[str]") -> Future:
        """Call destroy_activity on the requestor activity api."""

        awaitable = Future()

        def _call_destroy_activity(probe: Probe):
            activity_id = fut_activity_id.result()

            result = probe.activity.control.destroy_activity(activity_id)
            awaitable.set_result(result)
            return result

        step = CallableStep(
            name="destroy_activity",
            timeout=10,
            probes=self._probes,
            callback=_call_destroy_activity,
        )
        self._steps.append(step)
        return awaitable

    def gather_invoice(self, fut_agreement_id: "Future[str]") -> "Future[InvoiceEvent]":
        """Call gather_invoice on the requestor payment api."""

        awaitable = Future()

        def _call_gather_invoice(probe: Probe) -> InvoiceEvent:
            agreement_id = fut_agreement_id.result()

            invoice_events = []
            while len(invoice_events) == 0:
                time.sleep(2.0)
                invoice_events = (
                    probe.payment.get_received_invoices()
                )  # to be replaced by requestor.events.waitUntil(InvoiceReceivedEvent)
                logger.debug(f"Gathered invoice_event {invoice_events}")
                invoice_events = list(
                    filter(lambda x: x.agreement_id == agreement_id, invoice_events)
                )
                logger.debug(f"filtered invoice_event {invoice_events}")

            invoice_event = invoice_events[0]
            awaitable.set_result(invoice_event)
            return invoice_event

        step = CallableStep(
            name="gather_invoice",
            timeout=10,
            probes=self._probes,
            callback=_call_gather_invoice,
        )
        self._steps.append(step)
        return awaitable

    def pay_invoice(self, fut_invoice_event: "Future[InvoiceEvent]") -> Future:
        """Call accept_invoice on the requestor payment api."""

        awaitable = Future()

        def _call_pay_invoice(probe: Probe):
            invoice_event = fut_invoice_event.result()

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
            result = probe.payment.accept_invoice(invoice_event.invoice_id, acceptance)
            logger.debug(
                f"Accepted invoice. id={invoice_event.invoice_id}, result={result}"
            )

            awaitable.set_result(result)
            return result

        step = CallableStep(
            name="pay_invoice",
            timeout=10,
            probes=self._probes,
            callback=_call_pay_invoice,
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
