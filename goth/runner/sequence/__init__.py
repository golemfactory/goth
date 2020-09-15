"""Classes for running test scenarios based on sequences of steps."""
import asyncio
import logging
from pathlib import Path
import time
from typing import List, Optional

from goth.runner import Role, Runner
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.sequence.step import Step
from goth.runner.sequence.builder import ProbeStepBuilder

logger = logging.getLogger(__name__)


class SequenceRunner(Runner):
    """A runner that executes a scenario consisting of a sequence of sequence."""

    steps: List[Step]
    """The list of sequence to be awaited, sequence of the scenario to be executed."""

    def __init__(
        self,
        topology: List[YagnaContainerConfig],
        api_assertions_module: Optional[str],
        logs_path: Path,
        assets_path: Optional[Path],
    ):
        super().__init__(topology, api_assertions_module, logs_path, assets_path)
        self.steps = []

    def get_builder(
        self, role: Optional[Role] = None, name: Optional[str] = ""
    ) -> ProbeStepBuilder:
        """Create a ProbeStepBuilder for probes with the specified criteria."""
        probes = self.get_probes(role, name)
        return ProbeStepBuilder(self.steps, probes)

    async def run_scenario(self):
        """Start the nodes, run the scenario, then stop the nodes and clean up."""

        self._start_nodes()
        try:
            for step in self.steps:
                start_time = time.time()
                self.logger.info("running step. step=%s", step)
                try:
                    await asyncio.wait_for(step.tick(), step.timeout)
                    self.check_assertion_errors()
                    step_time = time.time() - start_time
                    self.logger.debug(
                        "finished step. step=%s, time=%s", step, step_time
                    )
                except Exception as exc:
                    step_time = time.time() - start_time
                    self.logger.error(
                        "step %s raised %s in %s",
                        step,
                        exc.__class__.__name__,
                        step_time,
                    )
                    raise
        finally:
            # Sleep to let the logs be saved
            await asyncio.sleep(2.0)
            for probe in self.probes:
                self.logger.info("stopping probe. name=%s", probe.name)
                await probe.stop()

            await self._stop_static_monitors()

            self.proxy.stop()

            # Stopping the proxy and probe log monitors triggered evaluation
            # of assertions at the "end of events". There may be some new failures.
            self.check_assertion_errors()
