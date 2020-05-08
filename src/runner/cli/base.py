"""Classes for running commands in a docker container and some utility functions"""

import json
import logging
from typing import Any, List, Optional, Tuple

from docker.models.containers import Container, ExecResult

from src.runner.exceptions import CommandError


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DockerCommandRunner:
    """A wrapper for executing a command in a docker container"""

    def __init__(self, container: Container, command: str):
        self.container = container
        self.command = command

    def run_command(self, *cmd_args, **kwargs) -> str:
        """Run the command with `cmd_args`. Return its output on success,
        raise `CommandError` on error.
        """

        result = self.run_command_no_throw(*cmd_args, **kwargs)
        if result.exit_code != 0:
            raise CommandError(result.output.decode())
        return result.output

    def run_command_no_throw(self, *cmd_args, **kwargs) -> ExecResult:
        """Run the command with `cmd_args`. Return its `ExecResult`.
        """

        cmd_line = f"{self.command} {' '.join(cmd_args)}"
        logger.debug("[%s] command: '%s'", self.container.name, cmd_line)
        return self.container.exec_run(cmd_line, **kwargs)


class DockerJSONCommandRunner(DockerCommandRunner):
    """Adds method for running commands with `--json` flag."""

    def run_json_command(self, *cmd_args, **kwargs) -> Any:
        """Add `--json` flag to command arguments and run the command.
        Parse the command output as JSON and return it.
        """

        if "--json" not in cmd_args:
            cmd_args = *cmd_args, "--json"
        output = self.run_command(*cmd_args, **kwargs)
        return json.loads(output)


def parse_json_table(output_dict: dict) -> List[dict]:
    """Parse a table in JSON format as returned by some `yagna` subcommands."""

    headers: Optional[list] = output_dict.get("headers")
    values: Optional[list] = output_dict.get("values")

    if not headers or not values:
        raise ValueError(json.dumps(output_dict))

    result = []
    row: Tuple[str]
    for row in values:
        row_dict = {}
        for i, key in enumerate(headers):
            row_dict[key] = row[i]
        result.append(row_dict)

    return result


def unwrap_ok_err_json(output_dict: dict) -> dict:
    """Parse `{ "Ok": <result>, "Err": <error>}` JSON; return `<result>`
    or raise `CommandError(<error>)`.
    """

    if "Ok" in output_dict:
        return output_dict["Ok"]
    if "Err" in output_dict:
        raise CommandError(json.dumps(output_dict["Err"]))
    raise ValueError(json.dumps(output_dict))
