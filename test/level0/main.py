#!/usr/bin/env python3

import json
from typing import List, Optional, Tuple, Union

import docker
from docker.models.containers import Container, ExecResult


class CommandError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ContainerNotFoundError(Exception):
    pass


def parse_json_table(output_dict: dict) -> List[dict]:
    headers: Optional[list] = output_dict.get("headers")
    values: Optional[list] = output_dict.get("values")

    if not headers or not values:
        return []

    result = []
    row: Tuple[str]
    for row in values:
        row_dict = {}
        for i, key in enumerate(headers):
            row_dict[key] = row[i]
        result.append(row_dict)

    return result


def run_command(container: Container, cmd: str, **kwargs) -> ExecResult:
    if "--json" not in cmd:
        cmd += " --json"

    result: ExecResult = container.exec_run(cmd, **kwargs)
    if result.exit_code != 0:
        raise CommandError(result.output.decode())

    return result


def list_app_keys(container: Container):
    result = run_command(container, "yagna app-key list")
    return parse_json_table(json.loads(result.output))


def create_app_key(container: Container, key_name: str = "test-key") -> str:
    result = run_command(container, f"yagna app-key create {key_name}")
    return result.output.decode()


def get_container(client, name: str) -> Container:
    container = next(filter(lambda c: name in c.name, client.containers.list()))
    if not container:
        raise ContainerNotFoundError()
    return container


def scan_logs(container: Container, query: str):
    for line in container.logs(stream=True, follow=True, tail=10):
        print(line.decode())


if __name__ == "__main__":
    client = docker.from_env()
    requestor = get_container(client, "requestor")
    print(create_app_key(requestor))
