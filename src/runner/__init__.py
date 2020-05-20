from collections import defaultdict
from itertools import chain
import logging
from pathlib import Path
from typing import Dict, List

import docker

from src.runner.container import YagnaContainer
from src.runner.log import configure_logging
from src.runner.probe import Probe, Role

configure_logging()
logger = logging.getLogger(__name__)


class Runner:

    # Path to directory containing yagna assets which should be mounted in containers
    assets_path: Path

    docker_client: docker.DockerClient

    # Probes used for the test run, identified by their role names
    probes: Dict[Role, List[Probe]]

    def __init__(self, assets_path: Path):
        self.assets_path = assets_path
        self.docker_client = docker.from_env()
        self.probes = defaultdict(list)

    def run_nodes(self, scenario):
        for role, count in scenario.nodes.items():
            for c in range(count):
                container = YagnaContainer(
                    client=self.docker_client,
                    name=role.name,
                    volumes={
                        str(self.assets_path): "/asset",
                        f"{self.assets_path}/presets.json": "/presets.json",
                    },
                    ordinal=c + 1,
                )
                self.probes[role].append(Probe(container.run(), role))

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
