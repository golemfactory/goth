"""Helpers to build steps on the runner attached to different probes."""

import logging
import re
from typing import List

from goth.assertions import EventStream
from goth.runner.log_monitor import LogEvent
from goth.runner.probe import Probe

logger = logging.getLogger(__name__)

LogEvents = EventStream[LogEvent]


class ProbeStepBuilder:
    """Helper for creating test steps to be ran inside the runner."""

    def __init__(self, steps, probes: List[Probe]):
        self._steps = steps
        self._probes = probes

    def wait_for_offer_subscribed(self):
        """Wait until the provider agent subscribes to the offer."""
        step_result = []
        for probe in self._probes:
            step = assert_message_starts_with("Subscribed offer")
            result = probe.agent_logs.add_assertion(step)
            step_result.append(result)
        self._steps.append(step_result)

    def wait_for_proposal_accepted(self):
        """Wait until the provider agent accepts the proposal."""
        self._steps.append((_wait_for_proposal_accepted, self._probes))

    def wait_for_agreement_approved(self):
        """Wait until the provider agent accepts the agreement."""
        self._steps.append((_wait_for_agreement_approved, self._probes))

    def wait_for_exeunit_started(self):
        """Wait until the provider agent starts the exe-unit."""
        self._steps.append((_wait_for_exeunit_started, self._probes))

    def wait_for_exeunit_finished(self):
        """Wait until exe-unit finishes."""
        self._steps.append((_wait_for_exeunit_finished, self._probes))

    def wait_for_invoice_sent(self):
        """Wait until the invoice is sent."""
        self._steps.append((_wait_for_invoice_sent, self._probes))


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


async def assert_message_starts_with_and_wait(probe, needle):
    """Attaches an assertion to the probe and wait for the needle to be found."""

    probe.agent_logs.add_assertions([assert_message_starts_with(needle)])
    await probe.agent_logs.await_assertions()


# --- ASYNC PROBE ACTIONS --- #
# TODO: Move to own file


async def _wait_for_offer_subscribed(probe: Probe):
    logger.info("waiting for offer to be subscribed")
    await assert_message_starts_with_and_wait(probe, "Subscribed offer")


async def _wait_for_proposal_accepted(probe: Probe):
    logger.info("waiting for proposal to be accepted")
    await assert_message_starts_with_and_wait(probe, "Decided to AcceptProposal")
    logger.info("proposal accepted")


async def _wait_for_agreement_approved(probe: Probe):
    logger.info("waiting for agreement to be app roved")
    await assert_message_starts_with_and_wait(probe, "Decided to ApproveAgreement")
    logger.info("agreement approved")


async def _wait_for_exeunit_started(probe: Probe):
    logger.info("waiting for exe-unit to start")
    await assert_message_starts_with_and_wait(probe, r"\[ExeUnit\](.+)Started$")
    logger.info("exe-unit started")


async def _wait_for_exeunit_finished(probe: Probe):
    logger.info("waiting for exe-unit to finish")
    await assert_message_starts_with_and_wait(
        probe, "ExeUnit process exited with status Finished - exit code: 0"
    )
    logger.info("exe-unit finished")


async def _wait_for_invoice_sent(probe: Probe):
    logger.info("waiting for invoice to be sent")
    await assert_message_starts_with_and_wait(probe, r"Invoice (.+) sent")
    logger.info("invoice sent")
