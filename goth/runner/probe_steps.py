"""Helpers to build steps on the runner attached to different probes."""

import abc
import asyncio
from datetime import datetime, timedelta
import logging
import json
import os
from pathlib import Path
import re
import time
from typing import List

from goth.assertions import EventStream, Assertion
from goth.runner.log_monitor import LogEvent
from goth.runner.probe import Probe

from openapi_market_client import Demand, Proposal, AgreementProposal
from openapi_activity_client import ExeScriptRequest

logger = logging.getLogger(__name__)

LogEvents = EventStream[LogEvent]


class Step(abc.ABC):
    """Step to be awaited in the runner."""

    def __init__(self, name: str, timeout: int):
        self.name = name
        self.timeout = timeout

    @abc.abstractmethod
    def tick(self) -> bool:
        """Return `True` iff this step has been completed.

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

    def tick(self) -> bool:
        """Check if all required awaitables are done for this step.

        For the AssertionStep this means all assertions are marked as done
        """
        return all(a.done for a in self.assertions)


class CallableStep(Step):
    """Step that executes apython function call on all `probes`."""

    probes: List[Probe]
    """Probes to execute `callable(probe)` for."""
    callback: callable

    def setup_callback(self, probes, callback):
        """Configure this step, set probes and callback to be executed on tick()."""

        self.probes = probes
        self.callback = callback

    def tick(self) -> bool:
        """Check if all required awaitables are done for this step.

        For the CallableStep this means the callback is executed for each probe
        """
        logger.debug("tick()")
        for probe in self.probes:
            res = self.callback(probe)
            logger.debug("result=%r", res)
        return True


class ProbeStepBuilder:
    """Helper for creating test steps to be ran inside the runner."""

    def __init__(self, steps, probes: List[Probe]):
        self._steps: List[Step] = steps
        self._probes = probes

        # Requestor only
        my_path = os.path.abspath(os.path.dirname(__file__))
        self.exe_script_file = Path(
            my_path + "/../../test/level0/asset/exe_script.json"
        )
        logger.debug(f"exe_script read. contents={self.exe_script_file}")

    def log(self, fut):
        """Log the contents of the future."""

        def _call_log(probe):
            contents = fut.result()
            logger.debug("probe= %r, contents=%r", probe, contents)

        step = CallableStep(name="wait_for_proposal", timeout=10)
        step.setup_callback(self._probes, _call_log)
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

    def wait_for_exeunit_started(self):
        """Wait until the provider agent starts the exe-unit."""
        self._wait_for_log("wait_for_exeunit_started", r"\[ExeUnit\](.+)Started$")

    def wait_for_exeunit_finished(self):
        """Wait until exe-unit finishes."""
        self._wait_for_log(
            "wait_for_exeunit_finished",
            "ExeUnit process exited with status Finished - exit code: 0",
            timeout=60,
        )

    def wait_for_invoice_sent(self):
        """Wait until the invoice is sent."""
        self._wait_for_log("wait_for_invoice_sent", r"Invoice (.+) sent")

    def wait_for_invoice_paid(self):
        """Wait until the invoice is sent."""
        self._wait_for_log(
            "wait_for_invoice_paid",
            "Invoice .+? for agreement .+? was paid",
            timeout=60 * 5,
        )

    def _wait_for_log(self, name: str, message: str, timeout: int = 10):
        step = AssertionStep(name, timeout)
        for probe in self._probes:
            assertion = assert_message_starts_with(message)
            result = probe.agent_logs.add_assertion(assertion)
            step.add_assertion(result)
        self._steps.append(step)

    # --- REQUESTOR --- #

    def init_payment(self):
        """Call collect_offers on the requestor market api."""

        def _call_init_payment(probe):
            result = probe.cli.payment_init(requestor_mode=True)
            return result

        step = CallableStep(name="init_payment", timeout=120)
        step.setup_callback(self._probes, _call_init_payment)
        self._steps.append(step)

    def subscribe_demand(self):
        """Call subscribe demand on the requestor market api."""
        package = (
            "hash://sha3:d5e31b2eed628572a5898bf8c34447644bfc4b5130cfc1e4f10aeaa1"
            ":http://34.244.4.185:8000/rust-wasi-tutorial.zip"
        )
        constraints = (
            "(&(golem.inf.mem.gib>0.5)(golem.inf.storage.gib>1)"
            "(golem.com.pricing.model=linear))"
        )

        awaitable = asyncio.Future()

        def _call_subscribe_demand(probe):
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

        step = CallableStep(name="subscribe_demand", timeout=10)
        step.setup_callback(self._probes, _call_subscribe_demand)
        self._steps.append(step)
        return awaitable

    def wait_for_proposal(self, fut_subscription_id):
        """Call collect_offers on the requestor market api."""

        awaitable = asyncio.Future()

        def _call_subscribe_demand(probe):
            subscription_id, _ = fut_subscription_id.result()
            proposal = None
            while proposal is None:
                result_offers = probe.market.collect_offers(subscription_id)
                logger.debug(
                    f"collect_offers({subscription_id}). proposal={result_offers}"
                )
                if result_offers:
                    proposal = result_offers[0].proposal
                else:
                    logger.debug(f"Waiting on proposal... {result_offers}")
                    time.sleep(1.0)
            awaitable.set_result(proposal)
            return proposal

        step = CallableStep(name="wait_for_proposal", timeout=10)
        step.setup_callback(self._probes, _call_subscribe_demand)
        self._steps.append(step)
        return awaitable

    def counter_proposal(self, fut_subscription_id, fut_proposal):
        """Call collect_offers on the requestor market api."""

        awaitable = asyncio.Future()

        def _call_subscribe_demand(probe):
            subscription_id, demand = fut_subscription_id.result()
            provider_proposal = fut_proposal.result()

            # TODO: Would be nice to have the original demand here
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

        step = CallableStep(name="counter_proposal", timeout=10)
        step.setup_callback(self._probes, _call_subscribe_demand)
        self._steps.append(step)
        return awaitable

    def create_agreement(self, fut_proposal):
        """Call collect_offers on the requestor market api."""

        awaitable = asyncio.Future()

        def _call_create_agreement(probe):
            proposal = fut_proposal.result()

            valid_to = str(datetime.utcnow() + timedelta(days=1)) + "Z"
            logger.debug(f"valid_to={valid_to}")
            agreement_proposal = AgreementProposal(
                proposal_id=proposal.proposal_id, valid_to=valid_to
            )

            agreement_id = probe.market.create_agreement(agreement_proposal)
            awaitable.set_result(agreement_id)
            return agreement_id

        step = CallableStep(name="create_agreement", timeout=10)
        step.setup_callback(self._probes, _call_create_agreement)
        self._steps.append(step)
        return awaitable

    def confirm_agreement(self, fut_agreement_id):
        """Call collect_offers on the requestor market api."""

        awaitable = asyncio.Future()

        def _call_confirm_agreement(probe):
            agreement_id = fut_agreement_id.result()
            result = probe.market.confirm_agreement(agreement_id)
            awaitable.set_result(result)
            return result

        step = CallableStep(name="confirm_agreement", timeout=10)
        step.setup_callback(self._probes, _call_confirm_agreement)
        self._steps.append(step)
        return awaitable

    def create_activity(self, fut_agreement_id):
        """Call create_activity on the requestor activity api."""

        awaitable = asyncio.Future()

        def _call_create_activity(probe):
            agreement_id = fut_agreement_id.result()
            logger.debug("Creating activity... agreement_id=%s", agreement_id)
            activity_id = probe.activity.control.create_activity(agreement_id)
            logger.debug("Activity created agreement_id=%s", agreement_id)
            awaitable.set_result(activity_id)
            return activity_id

        step = CallableStep(name="create_activity", timeout=10)
        step.setup_callback(self._probes, _call_create_activity)
        self._steps.append(step)
        return awaitable

    def call_exec(self, fut_activity_id):
        """Call call_exec on the requestor activity api."""

        awaitable = asyncio.Future()

        def _call_call_exec(probe):
            activity_id = fut_activity_id.result()
            exe_script_txt = self.exe_script_file.read_text()
            logger.debug(f"exe_script read. contents={exe_script_txt}")

            batch_id = probe.activity.control.call_exec(
                activity_id, ExeScriptRequest(exe_script_txt)
            )
            awaitable.set_result(batch_id)
            return batch_id

        step = CallableStep(name="call_exec", timeout=10)
        step.setup_callback(self._probes, _call_call_exec)
        self._steps.append(step)
        return awaitable

    def collect_results(self, fut_activity_id, fut_batch_id):
        """Call collect_results on the requestor activity api."""

        awaitable = asyncio.Future()

        def _call_collect_results(probe):
            activity_id = fut_batch_id.result()
            batch_id = fut_activity_id.result()

            commands_cnt = len(json.loads(self.exe_script_txt))
            state = probe.activity.state.get_activity_state(activity_id)
            logger.debug(f"state. result={state}")
            results = probe.activity.control.get_exec_batch_results(
                activity_id, batch_id
            )
            logger.debug(f"poll batch results. result={results}")

            while len(results) < commands_cnt:
                time.sleep(1.0)
                state = probe.activity.state.get_activity_state(activity_id)
                logger.debug(f"state. result={state}")
                results = probe.activity.control.get_exec_batch_results(
                    activity_id, batch_id
                )  # TODO: requestor.events.waitUntil(ExecScriptCommandFinishedEvent)
                logger.debug(f"poll batch results. result={results}")

            batch_id = fut_batch_id.result()
            my_path = os.path.abspath(os.path.dirname(__file__))
            exe_script_file = Path(my_path + "/../asset/exe_script.json")
            logger.debug(f"exe_script read. contents={exe_script_file}")
            exe_script_txt = exe_script_file.read_text()
            logger.debug(f"exe_script read. contents={exe_script_txt}")

            batch_id = probe.activity.control.collect_results(
                batch_id, ExeScriptRequest(exe_script_txt)
            )
            awaitable.set_result(batch_id)
            return batch_id

        step = CallableStep(name="collect_results", timeout=10)
        step.setup_callback(self._probes, _call_collect_results)
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
