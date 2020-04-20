import json
import logging
from threading import Thread
from typing import Dict

import docker
from docker.models.containers import Container, ExecResult

from runner import command
from runner.exceptions import CommandError, ContainerNotFoundError
from runner.node import Node, Role

logger = logging.getLogger(__name__)


class TestScenario:
    def __init__(self):
        self.keys: Dict[str, str] = {}
        self.ids: Dict[str, str] = {}
        self.steps = [
            (self.create_app_key, Role.requestor),
            (self.create_app_key, Role.provider),
            (self.get_id, Role.requestor),
            (self.get_id, Role.provider),
            (self.start_provider, Role.provider),
            (self.start_requestor, Role.requestor),
        ]

    def get_id(self, node: Node) -> str:
        ids = node.cli.get_ids()
        default_id = next(filter(lambda i: i["default"] == "X", ids))
        address = default_id["address"]
        self.ids[node.name] = address
        return address

    def create_app_key(self, node: Node, key_name: str = "test-key") -> str:
        logger.info("attempting to create app-key. key_name=%s", key_name)
        try:
            key = node.cli.create_app_key(key_name)
        except CommandError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.warning("app-key already exists. key_name=%s", key_name)
                app_key: dict = next(
                    filter(lambda k: k["name"] == key_name, node.cli.get_app_keys())
                )
                key = app_key["key"]

        logger.info("app-key=%s", key)
        self.keys[node.name] = key
        return key

    def start_provider(self, node: Node):
        logger.info("starting provider agent")

        def follow_logs(node):
            result = node.cli.start_provider_agent(
                self.keys[node.name], self.ids[node.name]
            )
            for line in result.output:
                print(line.decode())

        Thread(target=follow_logs, args=(node,)).start()

    def start_requestor(self, node: Node):
        logger.info("starting requestor agent")
        result = node.cli.start_requestor_agent(self.keys[node.name])
        for line in result.output:
            print(line.decode())


class TestRunner:
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

    def run(self, scenario: TestScenario):
        self.nodes = self.get_nodes()
        for step, role in scenario.steps:
            logger.debug(f"running step: {step}")
            result = step(node=self.nodes[role.name])
