"""Classes for running commands in a docker container and some utility functions."""

import json
import logging
import shlex
from typing import Dict, List, Optional, Tuple, Type, TypeVar, TYPE_CHECKING

from docker.models.containers import ExecResult

from goth.runner.exceptions import CommandError

if TYPE_CHECKING:
    from goth.runner.container import DockerContainer


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DockerCommandRunner:
    """A wrapper for executing a command in a docker container."""

    def __init__(self, container: "DockerContainer", command: str):
        self.container = container
        self.command = command

    def run_command(self, *cmd_args: str) -> Tuple[str, str]:
        """Run the command with `cmd_args`.

        Return a pair of strings containing the standard output and standard error of
        the command on success, or raise `CommandError` on error.
        """

        result = self.run_command_no_throw(*cmd_args)
        # Command's stdout or stderr may be None
        cmd_stderr = result.output[1].decode() if result.output[1] else ""
        cmd_stdout = result.output[0].decode() if result.output[0] else ""
        if result.exit_code != 0:
            raise CommandError(cmd_stderr)
        return cmd_stdout, cmd_stderr

    def run_command_no_throw(self, *cmd_args: str) -> ExecResult:
        """Run the command with `cmd_args`; return its `ExecResult`."""

        cmd_line = f"{self.command} {' '.join(cmd_args)}"
        logger.debug("[%s] command: '%s'", self.container.name, cmd_line)
        return self.container.exec_run(cmd_line, demux=True)


T = TypeVar("T")


class DockerJSONCommandRunner(DockerCommandRunner):
    """Adds method for running commands with `--json` flag."""

    def run_json_command(self, result_type: Type[T], *cmd_args: str) -> T:
        """Add `--json` flag to command arguments and run the command.

        Parse the command output as JSON and return it.
        """

        if "--json" not in cmd_args:
            cmd_args = *cmd_args, "--json"
        cmd_stdout, _ = self.run_command(*cmd_args)
        obj = json.loads(cmd_stdout)
        if isinstance(obj, result_type):
            return obj
        raise CommandError(
            f"Expected a {result_type.__name__} but command returned: {obj}"
        )


def make_args(obj: str, verb: str, *args: str, **opt_args) -> List[str]:
    """Build a list of positional and keyword arguments for a shell command."""

    cmd_args = [obj, verb]
    cmd_args.extend([shlex.quote(arg) for arg in args if arg])
    for key, value in opt_args.items():
        if value:
            cmd_args.extend([f"--{key}", shlex.quote(str(value))])
    return cmd_args


def parse_json_table(output_dict: dict) -> List[Dict[str, str]]:
    """Parse a table in JSON format as returned by some `yagna` subcommands."""

    headers: Optional[list] = output_dict.get("headers")
    values: Optional[list] = output_dict.get("values")

    if not headers or values is None:
        raise ValueError(json.dumps(output_dict))

    result = []
    row: Tuple[str]
    for row in values:
        row_dict = {}
        for i, key in enumerate(headers):
            row_dict[key] = row[i]
        result.append(row_dict)

    return result


U = TypeVar("U")


def unwrap_ok_err_json(output_dict: Dict[str, U]) -> U:
    """Parse `{ "Ok": <result>, "Err": <error>}` JSON; return `<result>`.

    or raise `CommandError(<error>)`.
    """

    if "Ok" in output_dict:
        return output_dict["Ok"]
    if "Err" in output_dict:
        raise CommandError(json.dumps(output_dict["Err"]))
    raise ValueError(json.dumps(output_dict))
