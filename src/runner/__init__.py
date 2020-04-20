import json
import logging
import re
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
        self.steps = [
            (self.create_app_key, Role.requestor),
            (self.create_app_key, Role.provider),
            (self.start_provider, Role.provider),
            (self.start_requestor, Role.requestor),
            (self.wait_for_proposal_accepted, Role.provider),
            (self.wait_for_agreement_approved, Role.provider),
            (self.wait_for_exeunit_started, Role.provider),
            (self.wait_for_exeunit_finished, Role.provider),
        ]

    def create_app_key(self, node: Node, key_name: str = "test-key"):
        logger.info("attempting to create app-key. key_name=%s", key_name)
        key = node.create_app_key(key_name)
        logger.info("app-key=%s", key)

    def start_provider(self, node: Node):
        logger.info("starting provider agent")
        node.start_provider_agent()
        node.agent_logs.wait_for_pattern(re.compile("^(.+)Subscribed offer.(.+)$"))

    def start_requestor(self, node: Node):
        logger.info("starting requestor agent")
        node.start_requestor_agent()

    def wait_for_proposal_accepted(self, node: Node):
        logger.info("waiting for proposal to be accepted")
        match = node.agent_logs.wait_for_pattern(
            re.compile("^(.+)decided to: AcceptProposal$")
        )
        logger.info("proposal accepted")

    def wait_for_agreement_approved(self, node: Node):
        logger.info("waiting for agreement to be approved")
        match = node.agent_logs.wait_for_pattern(
            re.compile("^(.+)decided to: ApproveAgreement$")
        )
        logger.info("agreement approved")

    def wait_for_exeunit_started(self, node: Node):
        logger.info("waiting for exe-unit to start")
        match = node.agent_logs.wait_for_pattern(re.compile("^\[ExeUnit\](.+)Started$"))
        logger.info("exe-unit started: %s", match.group(0))

    def wait_for_exeunit_finished(self, node: Node):
        logger.info("waiting for exe-unit to finish")
        match = node.agent_logs.wait_for_pattern(
            re.compile(
                "^(.+)ExeUnit process exited with status Finished - exit code: 0(.+)$"
            )
        )
        logger.info("exe-unit finished: %s", match.group(0))


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
