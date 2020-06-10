from collections import defaultdict
from itertools import chain
import logging
from pathlib import Path
from typing import Dict, List

import docker

from src.runner.log import configure_logging, create_file_logger, LogConfig
from src.runner.probe import Probe, Role


class Runner:

    assets_path: Path
    """ Path to directory containing yagna assets which should be mounted in
        containers """

    base_log_dir: Path
    """ Base directory for all log files created during this test run """

    probes: Dict[Role, List[Probe]]
    """ Probes used for the test run, identified by their role names """

    def __init__(self, assets_path: Path, logs_path: Path):
        self.assets_path = assets_path
        self.base_log_dir = logs_path
        self.probes = defaultdict(list)

        log_config = LogConfig(
            file_name="runner", base_dir=self.base_log_dir, level=logging.DEBUG
        )
        self.logger = create_file_logger(log_config)

    def _run_nodes(self, scenario):
        docker_client = docker.from_env()
        scenario_dir = self.base_log_dir / type(scenario).__name__
        scenario_dir.mkdir(exist_ok=True)

        for config in scenario.topology:
            config.assets_path = self.assets_path
            log_config = config.log_config or LogConfig(config.name)
            log_config.base_dir = scenario_dir

            probe = Probe(docker_client, config, log_config)
            self.probes[config.role].append(probe)
            probe.container.start()

    def run(self, scenario):
        self._run_nodes(scenario)

        try:
            for step, role in scenario.steps:
                self.logger.debug("running step. role=%s, step=%s", role, step)
                for probe in self.probes[role]:
                    step(probe=probe)
        finally:
            for probe in chain.from_iterable(self.probes.values()):
                self.logger.info("removing container. name=%s", probe.name)
                probe.container.remove(force=True)
