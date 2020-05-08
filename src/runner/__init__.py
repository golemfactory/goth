import logging
from pathlib import Path
from typing import Dict

import docker

from src.runner.container import YagnaContainer
from src.runner.log import configure_logging
from src.runner.node import Node, Role

configure_logging()
logger = logging.getLogger(__name__)


class Runner:

    # Path to directory containing yagna assets which should be mounted in containers
    assets_path: Path

    docker_client: docker.DockerClient

    # Nodes used for the test run, identified by their role names
    nodes: Dict[str, Node]

    def __init__(self, assets_path: Path):
        self.assets_path = assets_path
        self.docker_client = docker.from_env()
        self.nodes = {}

    def run_nodes(self):
        for role in Role:
            container = YagnaContainer(
                self.docker_client,
                role.name,
                {
                    str(self.assets_path): "/asset",
                    f"{self.assets_path}/presets.json": "/presets.json",
                },
            )
            self.nodes[role.name] = Node(container.run(), role)

    def run(self, scenario):
        self.run_nodes()
        for step, role in scenario.steps:
            logger.debug(f"running step: {step}")
            result = step(node=self.nodes[role.name])
