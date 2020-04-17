import json
import logging
from threading import Thread
from typing import Dict

from enum import Enum
import docker
from docker.models.containers import Container, ExecResult

from runner import command
from runner.exceptions import CommandError, ContainerNotFoundError

logger = logging.getLogger(__name__)


class Role(Enum):
    requestor = 0
    provider = 1


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

    def get_id(self, container: Container) -> str:
        ids = command.get_ids(container)
        default_id = next(filter(lambda i: i["default"] == "X", ids))
        address = default_id["address"]
        self.ids[container.name] = address
        return address

    def create_app_key(self, container: Container, key_name: str = "test-key") -> str:
        logger.info("attempting to create app-key. key_name=%s", key_name)
        try:
            key = command.create_app_key(container, key_name)
        except CommandError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.warning("app-key already exists. key_name=%s", key_name)
                app_key: dict = next(
                    filter(
                        lambda k: k["name"] == key_name, command.get_app_keys(container)
                    )
                )
                key = app_key["key"]

        logger.info("app-key=%s", key)
        self.keys[container.name] = key
        return key

    def start_provider(self, container: Container):
        logger.info("starting provider agent")

        def follow_logs(container):
            result = command.start_provider_agent(
                container, self.keys[container.name], self.ids[container.name]
            )
            for line in result.output:
                print(line.decode())

        Thread(target=follow_logs, args=(container,)).start()

    def start_requestor(self, container: Container):
        logger.info("starting requestor agent")
        result = command.start_requestor_agent(container, self.keys[container.name])
        for line in result.output:
            print(line.decode())


class TestRunner:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.containers = {}

    def get_containers(self) -> Dict[str, Container]:
        result = {}
        for role in Role:
            result[role.name] = self.get_container(role.name)

        return result

    def get_container(self, name: str) -> Container:
        container = next(
            filter(lambda c: name in c.name, self.docker_client.containers.list())
        )
        if not container:
            raise ContainerNotFoundError()
        return container

    def run(self, scenario: TestScenario):
        self.containers = self.get_containers()
        for step, role in scenario.steps:
            logger.debug(f"running step: {step}")
            result = step(container=self.containers[role.name])
