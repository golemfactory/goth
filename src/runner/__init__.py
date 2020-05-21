from collections import defaultdict
from itertools import chain
import logging
from pathlib import Path
from typing import Dict, List

import docker

from src.runner.log import configure_logging
from src.runner.probe import Probe, Role

configure_logging()
logger = logging.getLogger(__name__)


class Runner:

    # Path to directory containing yagna assets which should be mounted in containers
    assets_path: Path

    # Probes used for the test run, identified by their role names
    probes: Dict[Role, List[Probe]]

    def __init__(self, assets_path: Path):
        self.assets_path = assets_path
        self.probes = defaultdict(list)

    def run_nodes(self, scenario):
        docker_client = docker.from_env()
        for config in scenario.topology:
            config.assets_path = self.assets_path
            probe = Probe(docker_client, config)
            self.probes[config.role].append(probe)
            probe.container.run()

    def run(self, scenario):
        self.run_nodes(scenario)

        try:
            for step, role in scenario.steps:
                logger.debug("running step. role=%s, step=%s", role, step)
                for probe in self.probes[role]:
                    step(probe=probe)
        finally:
            for probe in chain.from_iterable(self.probes.values()):
                logger.info("removing container. name=%s", probe.name)
                probe.container.remove(force=True)
