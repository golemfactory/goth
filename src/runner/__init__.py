import json
import logging
import pytest
import time
from threading import Thread
from typing import Dict

from enum import Enum
import docker
from docker.models.containers import Container, ExecResult

from src.runner import command
from src.runner.exceptions import CommandError, ContainerNotFoundError

logger = logging.getLogger(__name__)

exception_raised = False
test_finished = False


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
            (self.wait_for_invoice, Role.provider),
        ]
        self.exception_raised = False

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

        def follow_logs():
            global exception_raised
            global test_finished
            result = command.start_provider_agent(
                container, self.keys[container.name], self.ids[container.name]
            )
            while result.exit_code is None:
                for line in result.output:
                    str_line = line.decode()
                    #logger.info(str_line)
                    if 'ERROR' in str_line:
                        print('ERROR')
                        exception_raised = True
                        raise Exception("ERROR")
                    if exception_raised or test_finished:
                        raise Exception('STOPPED')
                time.sleep(1.)
            logger.info("provider follow ended")

        self.provider_thread = Thread(target=follow_logs)
        self.provider_thread.start()

    def start_requestor(self, container: Container):
        logger.info("starting requestor agent")

        def follow_logs():
            global exception_raised
            global test_finished
            result = command.start_requestor_agent(container, self.keys[container.name])
            logger.info("follow_logs requestor agent")
            logger.info(result)
            while result.exit_code is None:
                for line in result.output:
                    str_line = line.decode()
                    logger.info(str_line)
                    if 'ERROR' in str_line:
                        print('ERROR')
                        exception_raised = True
                        raise Exception("ERROR")
                    elif 'yay!' in str_line:
                        test_finished = True
                        return
                    if exception_raised:
                        raise Exception('STOPPED')
                time.sleep(1.)
            container.reload()
            logger.info("requestor follow ended. exit_code=%r", result.exit_code)

        self.requestor_thread = Thread(target=follow_logs)
        self.requestor_thread.start()

    def wait_for_invoice(self, container: Container):
        global exception_raised
        global test_finished
        while not test_finished:
            logger.debug('tick')
            time.sleep(10.)
            if exception_raised:
                self._clean_threads()
                raise Exception("TEST FAILED")
        self._clean_threads()

    def _clean_threads(self):
        self.provider_thread.join()
        self.requestor_thread.join()




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
        logger.debug('get_container()')
        container = next(
            filter(lambda c: name in c.name, self.docker_client.containers.list())
        )
        if not container:
            raise ContainerNotFoundError()
        return container

    def run(self, scenario: TestScenario):
        logger.debug('run()')
        self.containers = self.get_containers()
        for step, role in scenario.steps:
            logger.debug(f"running step: {step}")
            result = step(container=self.containers[role.name])
