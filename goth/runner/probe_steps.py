"""Helpers to build steps on the runner attached to different probes."""

import abc
import logging
import re
from typing import List

from goth.assertions import EventStream, Assertion
from goth.runner.log_monitor import LogEvent
from goth.runner.probe import Probe

logger = logging.getLogger(__name__)

LogEvents = EventStream[LogEvent]


class Step(abc.ABC):
    """Step to be awaited in the runner."""

    def __init__(self, name: str, timeout: int):
        self.name = name
        self.timeout = timeout

    @abc.abstractmethod
    def is_done(self):
        """Check if all required awaitables are done for this step.

        Implemented in sub-classes of Step
        """

    def __str__(self):
        return f"{self.name}(timeout={self.timeout})"

    def __repr__(self):
        return f"<{type(self).__name__} name={self.name} timeout={self.timeout}>"


class AssertionStep(Step):
    """Step that holds a set of assertions to await."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._assertions: List[Assertion] = []

    def add_assertion(self, assertion: Assertion):
        """Add an assertion to be awaited in this step."""
        self._assertions.append(assertion)

    def is_done(self):
        """Check if all required awaitables are done for this step.

        For the AssertionStep this means all assertions are marked as done
        """
        return all(a.done for a in self._assertions)


class ProbeStepBuilder:
    """Helper for creating test steps to be ran inside the runner."""

    def __init__(self, steps, probes: List[Probe]):
        self._steps: List[Step] = steps
        self._probes = probes

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
        )

    def wait_for_invoice_sent(self):
        """Wait until the invoice is sent."""
        self._wait_for_log("wait_for_invoice_sent", r"Invoice (.+) sent")

    def _wait_for_log(self, name: str, message: str, timeout=10):
        step = AssertionStep(name, timeout)
        for probe in self._probes:
            assertion = assert_message_starts_with(message)
            result = probe.agent_logs.add_assertion(assertion)
            step.add_assertion(result)
        self._steps.append(step)
                    "golem.srv.comp.wasm.task_package": package,


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
