from typing import List, Optional, Tuple, Union

from docker.models.containers import Container, ExecResult

from runner.exceptions import CommandError


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
