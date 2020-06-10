from collections import defaultdict
from datetime import datetime, timezone
from itertools import chain
import logging
from pathlib import Path
from typing import Dict, List, Optional

import docker

from src.runner.log import configure_logging, LogConfig
from src.runner.probe import Probe, Role
from src.runner.container.proxy import ProxyContainer, ProxyContainerConfig
from src.runner.container.yagna import YagnaContainerConfig


class Runner:

    assets_path: Optional[Path]
    """ Path to directory containing yagna assets which should be mounted in
        containers """

    base_log_dir: Path
    """ Base directory for all log files created during this test run """

    probes: Dict[Role, List[Probe]]
    """ Probes used for the test run, identified by their role names """

    proxies: List[ProxyContainer]

    def __init__(self, assets_path: Optional[Path], logs_path: Path):

        self.assets_path = assets_path
        self.probes = defaultdict(list)
        self.proxies = []

        # Create a unique subdirectory for this test run
        date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
        self.base_log_dir = logs_path / f"yagna_integration_{date_str}"
        self.base_log_dir.mkdir(parents=True)

        configure_logging(self.base_log_dir)
        self.logger = logging.getLogger(__name__)

    async def run_scenario(self, scenario):
        self.logger.info("running scenario %s", type(scenario).__name__)
        self._run_nodes(scenario)
        try:
            for step, role in scenario.steps:
                for probe in self.probes[role]:
                    self.logger.debug("running step. probe=%s, role=%s, step=%s", probe, role, step)
                    result = step(probe=probe)
                    if result:
                        await result
        finally:
            for probe in chain.from_iterable(self.probes.values()):
                self.logger.info("removing container. name=%s", probe.name)
                probe.container.remove(force=True)
            for proxy in self.proxies:
                proxy.remove(force=True)

    def _run_nodes(self, scenario):
        docker_client = docker.from_env()
        scenario_dir = self.base_log_dir / type(scenario).__name__
        scenario_dir.mkdir(exist_ok=True)

        for config in scenario.topology:
            log_config = config.log_config or LogConfig(config.name)
            log_config.base_dir = scenario_dir
            if isinstance(config, YagnaContainerConfig):
                probe = Probe(docker_client, config, log_config, self.assets_path)
                self.probes[config.role].append(probe)
                probe.container.start()
            elif isinstance(config, ProxyContainerConfig):
                proxy = ProxyContainer(
                    docker_client, config, log_config, self.assets_path
                )
                self.proxies.append(proxy)
                proxy.start()
