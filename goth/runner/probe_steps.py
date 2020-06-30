""" Helpers to build steps on the runner attached to different probes  """

import logging
import re

from goth.assertions import EventStream
from goth.runner.log_monitor import LogEvent
from goth.runner.probe import Probe, Role

logger = logging.getLogger(__name__)

LogEvents = EventStream[LogEvent]


class ProbeStepBuilder:
    def __init__(self, steps, probes: Role):
        self._steps = steps
        self._probes = probes

    def wait_for_offer_subscribed(self):
        self._steps.append((wait_for_offer_subscribed, self._probes))

    def wait_for_proposal_accepted(self):
        self._steps.append((wait_for_proposal_accepted, self._probes))

    def wait_for_agreement_approved(self):
        self._steps.append((wait_for_agreement_approved, self._probes))

    def wait_for_exeunit_started(self):
        self._steps.append((wait_for_exeunit_started, self._probes))

    def wait_for_exeunit_finished(self):
        self._steps.append((wait_for_exeunit_finished, self._probes))

    def wait_for_invoice_sent(self):
        self._steps.append((wait_for_invoice_sent, self._probes))


### ASSERTIONS ###
# TODO: Move to own file


def assert_message_starts_with(needle: str):
    """Prepare an assertion that:
    Assert that a `LogEvent` with message starts with {needle} is found."""

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

    probe.agent_logs.add_assertions([assert_message_starts_with(needle)])
    await probe.agent_logs.await_assertions()


### ASYNC PROBE ACTIONS ###
# TODO: Move to own file


async def wait_for_offer_subscribed(probe: Probe):
    logger.info("waiting for offer to be subscribed")
    await assert_message_starts_with_and_wait(probe, "Subscribed offer")


async def wait_for_proposal_accepted(probe: Probe):
    logger.info("waiting for proposal to be accepted")
    await assert_message_starts_with_and_wait(probe, "Decided to AcceptProposal")
    logger.info("proposal accepted")


async def wait_for_agreement_approved(probe: Probe):
    logger.info("waiting for agreement to be app roved")
    await assert_message_starts_with_and_wait(probe, "Decided to ApproveAgreement")
    logger.info("agreement approved")


async def wait_for_exeunit_started(probe: Probe):
    logger.info("waiting for exe-unit to start")
    await assert_message_starts_with_and_wait(probe, r"\[ExeUnit\](.+)Started$")
    logger.info("exe-unit started")


async def wait_for_exeunit_finished(probe: Probe):
    logger.info("waiting for exe-unit to finish")
    await assert_message_starts_with_and_wait(
        probe, "ExeUnit process exited with status Finished - exit code: 0"
    )
    logger.info("exe-unit finished")


async def wait_for_invoice_sent(probe: Probe):
    logger.info("waiting for invoice to be sent")
    await assert_message_starts_with_and_wait(probe, r"Invoice (.+) sent")
    logger.info("invoice sent")
