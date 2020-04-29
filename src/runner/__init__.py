import logging
from typing import Dict

import docker

from src.runner.exceptions import ContainerNotFoundError
from src.runner.node import Node, Role

logger = logging.getLogger(__name__)


class Runner:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.nodes = {}

    def get_nodes(self) -> Dict[str, Node]:
        result = {}
        for role in Role:
            result[role.name] = self.get_node(role)

        return result

    def get_node(self, role: Role) -> Node:
        container = next(
            filter(lambda c: role.name in c.name, self.docker_client.containers.list())
        )
        if not container:
            raise ContainerNotFoundError()
        return Node(container, role)

    def run(self, scenario):
        self.nodes = self.get_nodes()
        for step, role in scenario.steps:
            logger.debug(f"running step: {step}")
            result = step(node=self.nodes[role.name])
