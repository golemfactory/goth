"""`ProviderProbe` subclasses for controlling provider nodes."""

from pathlib import Path
from typing import Optional
from docker import DockerClient

from goth.runner import Runner, YagnaContainerConfig
from goth.runner.probe import ProviderProbe
from goth.runner.log import LogConfig
from goth.runner.simple import step


class ProviderProbeWithLogSteps(ProviderProbe):
    """A provider probe with steps that wait for specific messages in agent logs."""

    def __init__(
        self,
        runner: Runner,
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
        preset_name: str = "default",
    ):
        super().__init__(runner, client, config, log_config, assets_path, preset_name)

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
        await self._wait_for_log(
            "ExeUnit process exited with status Finished - exit code: 0"
        )

    @step()
    async def wait_for_invoice_sent(self):
        """Wait until the invoice is sent."""
        await self._wait_for_log("Invoice (.+) sent")

    @step(default_timeout=300)
    async def wait_for_invoice_paid(self):
        """Wait until the invoice is paid."""
        await self._wait_for_log("Invoice .+? for agreement .+? was paid")
