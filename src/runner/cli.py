import json
from typing import List, Optional, Tuple

from docker.models.containers import Container, ExecResult

from src.runner.exceptions import CommandError


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


class YagnaCli:
    def __init__(self, container: Container):
        self.container = container

    def get_app_keys(self):
        result = self._run_json_cmd("yagna app-key list")
        return _parse_json_table(json.loads(result.output))

    def get_ids(self):
        result = self._run_json_cmd("yagna id list")
        return _parse_json_table(json.loads(result.output))

    def create_app_key(self, key_name: str) -> str:
        result = self._run_json_cmd(f"yagna app-key create {key_name}")
        return json.loads(result.output)

    def run_command(self, cmd: str, **kwargs):
        result: ExecResult = self.container.exec_run(cmd, **kwargs)
        if result.exit_code != 0:
            raise CommandError(result.output.decode())
        return result

    def _run_json_cmd(self, cmd: str) -> ExecResult:
        if "--json" not in cmd:
            cmd += " --json"

        return self.run_command(cmd)
