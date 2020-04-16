import json
import logging
from typing import List, Optional, Tuple

from docker.models.containers import Container, ExecResult

from runner.exceptions import CommandError

logger = logging.getLogger(__name__)


def get_app_keys(container: Container):
    result = _run_json_cmd(container, "yagna app-key list")
    return _parse_json_table(json.loads(result.output))


def get_ids(container: Container):
    result = _run_json_cmd(container, "yagna id list")
    return _parse_json_table(json.loads(result.output))


def create_app_key(container: Container, key_name: str) -> str:
    result = _run_json_cmd(container, f"yagna app-key create {key_name}")
    return json.loads(result.output)


def scan_logs(container: Container, query: str):
    for line in container.logs(stream=True, follow=True, tail=10):
        print(line.decode())


def start_provider_agent(container: Container, app_key: str, address: str):
    return container.exec_run(
        f"ya-provider --app-key {app_key} --credit-address {address}", stream=True,
    )


def start_requestor_agent(container: Container, app_key: str):
    return container.exec_run(f"ya-requestor --app-key {app_key}", stream=True)


def run_command(container: Container, cmd: str, **kwargs):
    result: ExecResult = container.exec_run(cmd, **kwargs)
    if result.exit_code != 0:
        raise CommandError(result.output.decode())
    return result


def _parse_json_table(output_dict: dict) -> List[dict]:
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


def _run_json_cmd(container: Container, cmd: str) -> ExecResult:
    if "--json" not in cmd:
        cmd += " --json"

    return run_command(container, cmd)
