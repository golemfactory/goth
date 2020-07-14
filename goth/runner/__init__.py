"""Test harness runner class, creating the nodes and running the scenario."""

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from itertools import chain
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import docker

from goth.assertions import TemporalAssertionError
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.log import configure_logging, LogConfig
from goth.runner.log_monitor import _create_file_logger
from goth.runner.probe import Probe, ProviderProbe, RequestorProbe, Role
from goth.runner.probe_steps import ProbeStepBuilder
from goth.runner.proxy import Proxy


class Runner:
    """Manages the nodes and runs the scenario on them."""

    assets_path: Optional[Path]
    """Path to directory containing yagna assets to be mounted in containers."""

    base_log_dir: Path
    """Base directory for all log files created during this test run."""

    probes: Dict[Role, List[Probe]]
    """Probes used for the test run, identified by their role names."""

    proxy: Optional[Proxy]
    """An embedded instance of mitmproxy."""

    def __init__(
        self,
        topology: List[YagnaContainerConfig],
        logs_path: Path,
        assets_path: Optional[Path],
    ):

        self.topology = topology
        self.assets_path = assets_path
        self.probes = defaultdict(list)
        self.proxy = None
        self.steps = []

        # Create a unique subdirectory for this test run
        date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
        self.base_log_dir = logs_path / f"yagna_integration_{date_str}"
        self.base_log_dir.mkdir(parents=True)

        configure_logging(self.base_log_dir)
        self.logger = logging.getLogger(__name__)
        self._run_nodes()

    def check_assertion_errors(self) -> None:
        """If any monitor reports an assertion error, raise the first error."""

        probes = chain.from_iterable(self.probes.values())
        monitors = chain.from_iterable(
            (
                (probe.container.logs for probe in probes),
                (probe.agent_logs for probe in probes),
                [self.proxy.monitor],
            )
        )
        failed = chain.from_iterable(
            monitor.failed for monitor in monitors if monitor is not None
        )
        for assertion in failed:
            # We assume all failed assertions were already reported
            # in their corresponding log files. Now we only need to raise
            # one of them to break the execution.
            raise TemporalAssertionError(
                f"Assertion '{assertion.name}' failed, cause: {assertion.result}"
            )

    async def run_scenario(self):
        """Start the nodes, run the scenario, then stop the nodes and clean up."""
        # self.logger.info("running scenario %s", type(self.scenario).__name__)
        try:
            for step, role in self.steps:
                # Collect awaitables to execute them at the same time
                awaitables = []
                self.logger.info(self.probes)
                for probe in self.probes[role]:
                    self.logger.debug(
                        "running step. probe=%s, role=%s, step=%s", probe, role, step
                    )
                    result = step(probe=probe)
                    if result:
                        awaitables.append(result)
                if awaitables:
                    await asyncio.gather(*awaitables, return_exceptions=True)

                self.check_assertion_errors()

        finally:
            # Sleep to let the logs be saved
            await asyncio.sleep(2.0)
            for probe in chain.from_iterable(self.probes.values()):
                self.logger.info("stopping probe. name=%s", probe.name)
                await probe.stop()

            self.proxy.stop()
            # Stopping the proxy triggered evaluation of assertions
            # "at the end of events".
            self.check_assertion_errors()

    def _run_nodes(self):

        docker_client = docker.from_env()
        test_name = os.environ.get("PYTEST_CURRENT_TEST")
        test_name = test_name.replace("::", "_")
        test_name = test_name.replace("/", "_")
        self.logger.info(test_name)
        scenario_dir = self.base_log_dir / test_name
        scenario_dir.mkdir(exist_ok=True)

        self.proxy = Proxy(
            logger=_create_proxy_logger(scenario_dir),
            assertions_module="asset.assertions.level0_assertions",
        )
        self.proxy.start()

        for config in self.topology:
            log_config = config.log_config or LogConfig(config.name)
            log_config.base_dir = scenario_dir

            if isinstance(config, YagnaContainerConfig):
                if config.role == Role.requestor:
                    probe = RequestorProbe(
                        docker_client, config, log_config, self.assets_path
                    )
                else:
                    probe = ProviderProbe(
                        docker_client, config, log_config, self.assets_path
                    )

                probe.start()
                self.probes[config.role].append(probe)

    def get_probes(self, role):
        """Create a ProbeStepBuilder for the requested role."""
        return ProbeStepBuilder(steps=self.steps, probes=role)


def _create_proxy_logger(scenario_dir):

    proxy_log_config = LogConfig("proxy")
    proxy_log_config.base_dir = scenario_dir
    proxy_log_config.formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s"
    )
    proxy_log_config.level = logging.DEBUG
    return _create_file_logger(proxy_log_config)
