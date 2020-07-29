"""A minimal POC runner implementation."""
import abc
import asyncio
from datetime import datetime, timedelta
import functools
import logging
from pathlib import Path
import re
import time
from typing import Generic, List, Optional, Tuple, TypeVar

from goth.assertions import EventStream
from goth.assertions.operators import eventually
from goth.runner import Runner
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.log_monitor import LogEvent
from goth.runner.probe import ProviderProbe, RequestorProbe

from openapi_market_client import AgreementProposal, Demand, Proposal
from openapi_activity_client import ExeScriptCommandResult, ExeScriptRequest


logger = logging.getLogger(__name__)


def step(default_timeout: float = 10.0):
    """Wrap a step function to provide logging."""

    def decorator(func):

        @functools.wraps(func)
        async def wrapper(*args, timeout: Optional[float] = None):
            timeout = timeout if timeout is not None else default_timeout
            start_time = time.time()
            logger.info("Running step '%s', timeout: %s", func.__name__, timeout)
            try:
                result = await asyncio.wait_for(func(*args), timeout=timeout)
                logger.info(
                    "Finished step '%s', result: %s, time: %s",
                    func.__name__, result, time.time() - start_time
                )
            except asyncio.TimeoutError as te:
                logger.exception(te)
                raise
            return result

        return wrapper

    return decorator


R = TypeVar("R", ProviderProbe, RequestorProbe)


class ProbeSteps(Generic[R], abc.ABC):
    """Wraps a probe and adds test scenario steps."""

    probe: R

    last_checked_line: int

    def __init__(self, probe: R):
        self.probe = probe
        self.last_checked_line = -1

    async def _wait_for_log(self, pattern: str, timeout: float = 1000):

        regex = re.compile(pattern)

        def predicate(log_event) -> bool:
            return regex.match(log_event.message) is not None

        # First examine log lines already seen
        while self.last_checked_line + 1 < len(self.probe.agent_logs.events):
            self.last_checked_line += 1
            log_event = self.probe.agent_logs.events[self.last_checked_line]
            if predicate(log_event):
                return True

        # Otherwise create an assertion that waits for a matching line
        async def coro(stream):
            try:
                await eventually(stream, predicate, timeout=timeout)
            finally:
                self.last_checked_line = len(stream.past_events) - 1

        assertion = self.probe.agent_logs.add_assertion(coro)

        while not assertion.done:
            await asyncio.sleep(0.1)

        if assertion.failed:
            raise assertion.result
        return assertion.result


class ProviderSteps(ProbeSteps[ProviderProbe]):
    """Adds steps specific to provider nodes."""

    def __init__(self, probe: ProviderProbe):
        super().__init__(probe)

    @step()
    async def wait_for_offer_subscribed(self):
        """Wait until the provider agent subscribes to the offer."""
        await self._wait_for_log("Subscribed offer")

    @step()
    async def wait_for_proposal_accepted(self):
        """Wait until the provider agent subscribes to the offer."""
        await self._wait_for_log("Decided to AcceptProposal")

    @step()
    async def wait_for_agreement_approved(self):
        """Wait until the provider agent subscribes to the offer."""
        await self._wait_for_log("Decided to ApproveAgreement")

    @step()
    async def wait_for_activity_created(self):
        """Wait until the provider agent subscribes to the offer."""
        await self._wait_for_log("Activity created")

    @step()
    async def wait_for_exeunit_started(self):
        """Wait until the provider agent starts the exe-unit."""
        await self._wait_for_log(r"\[ExeUnit\](.+)Started$")

    @step()
    async def wait_for_exeunit_finished(self):
        """Wait until exe-unit finishes."""
        await self._wait_for_log("ExeUnit process exited with status Finished - exit code: 0")

    @step()
    async def wait_for_invoice_sent(self):
        """Wait until the invoice is sent."""
        await self._wait_for_log("Invoice (.+) sent")

    @step(default_timeout=300)
    async def wait_for_invoice_paid(self):
        """Wait until the invoice is paid."""
        await self._wait_for_log("Invoice .+? for agreement .+? was paid")


class RequestorSteps(ProbeSteps[RequestorProbe]):
    """Adds steps specific to requestor nodes."""

    def __init__(self, probe: RequestorProbe):
        super().__init__(probe)

    @step()
    async def init_payment(self) -> str:
        """Call init_payment on the requestor CLI."""
        result = self.probe.cli.payment_init(requestor_mode=True)
        return result

    @step()
    async def subscribe_demand(self) -> Tuple[str, Demand]:
        """Call subscribe demand on the requestor market api."""

        package = (
            "hash://sha3:d5e31b2eed628572a5898bf8c34447644bfc4b5130cfc1e4f10aeaa1"
            ":http://34.244.4.185:8000/rust-wasi-tutorial.zip"
        )
        constraints = (
            "(&(golem.inf.mem.gib>0.5)(golem.inf.storage.gib>1)"
            "(golem.com.pricing.model=linear))"
        )

        demand = Demand(
            requestor_id=self.probe.address,
            properties={
                "golem.node.id.name": "test1",
                "golem.srv.comp.expiration": int(
                    (datetime.now() + timedelta(days=1)).timestamp() * 1000
                ),
                "golem.srv.comp.task_package": package,
            },
            constraints=constraints,
        )

        subscription_id = self.probe.market.subscribe_demand(demand)
        return subscription_id, demand

    @step()
    async def unsubscribe_demand(self, subscription_id: str) -> None:
        """Call unsubscribe demand on the requestor market api."""
        self.probe.market.unsubscribe_demand(subscription_id)

    @step()
    async def wait_for_proposals(self, subscription_id: str) -> List[Proposal]:
        """Call collect_offers on the requestor market api."""
        proposals = None

        while proposals is None:
            result_offers = self.probe.market.collect_offers(subscription_id)
            logger.debug(
                "collect_offers(%s). proposal=%r", subscription_id, result_offers,
            )
            if result_offers:
                proposals = [offer.proposal for offer in result_offers]
            else:
                logger.debug("Waiting on proposal... %r", result_offers)
                await asyncio.sleep(1.0)

        return proposals

    @step()
    async def counter_proposal(
            self, subscription_id: str, demand: Demand, provider_proposal: Proposal
    ) -> str:
        """Call counter_proposal_demand on the requestor market api."""

        proposal = Proposal(
            constraints=demand.constraints,
            properties=demand.properties,
            prev_proposal_id=provider_proposal.proposal_id,
        )

        counter_proposal = self.probe.market.counter_proposal_demand(
            subscription_id=subscription_id,
            proposal_id=provider_proposal.proposal_id,
            proposal=proposal,
        )

        return counter_proposal

    @step()
    async def create_agreement(self, proposal: Proposal) -> str:
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

        agreement_id = self.probe.market.create_agreement(agreement_proposal)
        return agreement_id

    @step()
    async def confirm_agreement(self, agreement_id: str) -> None:
        """Call confirm_agreement on the requestor market api."""
        self.probe.market.confirm_agreement(agreement_id)

    @step()
    async def create_activity(self, agreement_id: str) -> str:
        """Call create_activity on the requestor activity api."""
        activity_id = self.probe.activity.control.create_activity(agreement_id)
        return activity_id

    @step()
    async def call_exec(self, activity_id: str, exe_script: str) -> str:
        """Call call_exec on the requestor activity api."""
        script_request = ExeScriptRequest(exe_script)
        batch_id = self.probe.activity.control.call_exec(activity_id, script_request)
        return batch_id

    @step()
    async def collect_results(
            self, activity_id: str, batch_id: str, num_results: int
    ) -> List[ExeScriptCommandResult]:
        """Call collect_results on the requestor activity api."""

        results = self.probe.activity.control.get_exec_batch_results(
            activity_id, batch_id
        )
        while len(results) < num_results:
            time.sleep(1.0)
            results = self.probe.activity.control.get_exec_batch_results(
                activity_id, batch_id
            )
        return results

    @step()
    async def destroy_activity(self, activity_id: str) -> None:
        """Call destroy_activity on the requestor activity api."""
        self.probe.activity.control.destroy_activity(activity_id)


class SimpleRunner(Runner):
    """A minimal runner"""

    def __init__(
            self,
            topology: List[YagnaContainerConfig],
            api_assertions_module: Optional[str],
            logs_path: Path,
            assets_path: Optional[Path],
    ):
        super().__init__(topology, api_assertions_module, logs_path, assets_path)

    def get_probe(self, name: str) -> ProbeSteps:

        for probe in self.probes:
            if probe.name == name:
                if isinstance(probe, ProviderProbe):
                    wrapper_class = ProviderSteps
                elif isinstance(probe, RequestorProbe):
                    wrapper_class = RequestorSteps
                else:
                    assert False
                return wrapper_class(probe)

        raise KeyError(f"No such probe: {name}")

    async def __aenter__(self):
        self._start_nodes()

    async def __aexit__(self, *args):
        await asyncio.sleep(2.0)
        for probe in self.probes:
            self.logger.info("stopping probe. name=%s", probe.name)
            await probe.stop()

        self.proxy.stop()
        # Stopping the proxy triggered evaluation of assertions
        # "at the end of events".
        self.check_assertion_errors()


def assert_message_starts_with(pattern: str):
    """Return the "message.start_with" assertion with pre-compiled re `needle`.

    Prepare an assertion that:
    Assert that a `LogEvent` with message starts with {needle} is found.
    """

    # No need to add ^ in the regexp since .match( searches from the start
    regex = re.compile(pattern)

    async def _assert_starts_with(stream: EventStream[LogEvent]) -> int:

        async for event in stream:
            match = regex.match(event.message)
            if match:
                return len(stream.past_events)

        raise AssertionError(f"No message starts with '{pattern}'")

    return _assert_starts_with
