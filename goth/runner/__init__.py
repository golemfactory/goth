import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from itertools import chain
import logging
from pathlib import Path
from typing import Dict, List, Optional

import docker

from goth.assertions import TemporalAssertionError
from goth.runner.log import configure_logging, LogConfig, LOGGING_CONFIG
from goth.runner.log_monitor import _create_file_logger
from goth.runner.probe import Probe, Role
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.proxy import Proxy


class Runner:

    assets_path: Optional[Path]
    """ Path to directory containing yagna assets which should be mounted in
        containers """

    base_log_dir: Path
    """ Base directory for all log files created during this test run """

    probes: Dict[Role, List[Probe]]
    """ Probes used for the test run, identified by their role names """

    proxy: Optional[Proxy]
    """ An embedded instance of mitmproxy """

    def __init__(self, assets_path: Optional[Path], logs_path: Path):

        self.assets_path = assets_path
        self.probes = defaultdict(list)
        self.proxy = None

        # Create a unique subdirectory for this test run
        date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
        self.base_log_dir = logs_path / f"yagna_integration_{date_str}"
        self.base_log_dir.mkdir(parents=True)

        configure_logging(self.base_log_dir)
        self.logger = logging.getLogger(__name__)

    def check_assertion_errors(self) -> None:
        """If any monitor reports an assertion error, raise the first error"""

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

    async def run_scenario(self, scenario):

        self.logger.info("running scenario %s", type(scenario).__name__)
        self._run_nodes(scenario)
        try:
            for step, role in scenario.steps:
                # Collect awaitables to execute them at the same time
                awaitables = []
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
            for probe in chain.from_iterable(self.probes.values()):
                self.logger.info("stopping probe. name=%s", probe.name)
                await probe.stop()

            self.proxy.stop()
            # Stopping the proxy triggered evaluation of assertions
            # "at the end of events".
            self.check_assertion_errors()

    def _run_nodes(self, scenario):

        docker_client = docker.from_env()
        scenario_dir = self.base_log_dir / type(scenario).__name__
        scenario_dir.mkdir(exist_ok=True)

        self.proxy = Proxy(
            logger=_create_proxy_logger(scenario_dir),
            assertions_module="asset.assertions.level0_assertions",
        )
        self.proxy.start()

        for config in scenario.topology:
            log_config = config.log_config or LogConfig(config.name)
            log_config.base_dir = scenario_dir
            if isinstance(config, YagnaContainerConfig):
                probe = Probe(docker_client, config, log_config, self.assets_path)
                self.probes[config.role].append(probe)
                probe.container.start()


def _create_proxy_logger(scenario_dir):

    proxy_log_config = LogConfig("proxy")
    proxy_log_config.base_dir = scenario_dir
    proxy_log_config.formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s"
    )
    proxy_log_config.level = logging.DEBUG
    return _create_file_logger(proxy_log_config)
