import json
from typing import Dict

from enum import Enum
import docker
from docker.models.containers import Container, ExecResult

from runner.exceptions import ContainerNotFoundError
from runner.helpers import parse_json_table, run_command


class Role(Enum):
    requestor = 0
    provider = 1


class TestScenario:
    def __init__(self):
        self.steps = [
            (self.list_app_keys, Role.requestor),
            (self.create_app_key, Role.requestor),
            (self.list_app_keys, Role.requestor),
        ]

    def list_app_keys(self, container: Container):
        result = run_command(container, "yagna app-key list")
        return parse_json_table(json.loads(result.output))

    def create_app_key(self, container: Container, key_name: str = "test-key") -> str:
        result = run_command(container, f"yagna app-key create {key_name}")
        return result.output.decode()

    def scan_logs(self, container: Container, query: str):
        for line in container.logs(stream=True, follow=True, tail=10):
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
            print(f"running step: {step}")
            result = step(container=self.containers[role.name])
            print(result)
