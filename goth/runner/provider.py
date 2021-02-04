"""`ProviderProbe` subclasses for controlling provider nodes."""

from goth.runner import step
from goth.runner.probe import ProviderProbe


class ProviderProbeWithLogSteps(ProviderProbe):
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
        await self._wait_for_agent_log(r"\[ExeUnit\](.+)Supervisor initialized$")

    @step()
    async def wait_for_exeunit_finished(self):
        """Wait until exe-unit finishes."""
        await self._wait_for_agent_log(
            "ExeUnit process exited with status Finished - exit code: 0"
        )

    @step()
    async def wait_for_invoice_sent(self):
        """Wait until the invoice is sent."""
        await self._wait_for_agent_log("Invoice (.+) sent")

    @step(default_timeout=300)
    async def wait_for_invoice_paid(self):
        """Wait until the invoice is paid."""
        await self._wait_for_agent_log("Invoice .+? for agreement .+? was paid")
