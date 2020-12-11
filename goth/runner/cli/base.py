"""Classes for running commands in a docker container and some utility functions."""

from dataclasses import dataclass
import json
import logging
import shlex
import subprocess
from typing import Dict, List, Optional, Tuple, Type, TypeVar, TYPE_CHECKING

from docker.models.containers import ExecResult

from goth.runner.exceptions import CommandError

if TYPE_CHECKING:
    from goth.runner.container import DockerContainer


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass(frozen=True)
class CommandResult:
    """Represents the result of a shell command."""

    exit_code: int
    stdout: bytes
    stderr: bytes


class CommandRunner:
    """Helper class for running shell commands on the host machine."""

    command: str
    """Name of the executable this runner instance will use."""

    def __init__(self, command: str):
        self.command = command

    def run_command(self, *cmd_args: str) -> Tuple[str, str]:
        """Run the command with arguments given in `cmd_args`.

        Return a pair of strings containing the standard output and standard error of
        the command on success, or raise `CommandError` on non-zero exit code.
        """

        result = self.run_command_no_throw(*cmd_args)
        # Command's stdout or stderr may be None
        cmd_stderr = result.stderr.decode() if result.stderr else ""
        cmd_stdout = result.stdout.decode() if result.stdout else ""

        if result.exit_code != 0:
            raise CommandError(cmd_stderr)

        return cmd_stdout, cmd_stderr

    def run_command_no_throw(self, *cmd_args: str) -> CommandResult:
        """Run command with `cmd_args` without raising an exception on failure."""

        cmd_line = list(cmd_args)
        cmd_line.insert(0, self.command)
        logger.debug("[%s] command: '%s'", cmd_line)
        result = subprocess.run(cmd_line, capture_output=True)
        return CommandResult(result.returncode, result.stdout, result.stderr)


class DockerCommandRunner(CommandRunner):
    """Helper class for running shell commands in a Docker container."""

    container: "DockerContainer"

    def __init__(self, container: "DockerContainer", command: str):
        super().__init__(command)
        self.container = container

    def run_command_no_throw(self, *cmd_args: str) -> CommandResult:
        """Run command with `cmd_args` without raising an exception on failure."""

        cmd_line = f"{self.command} {' '.join(cmd_args)}"
        logger.debug("[%s] command: '%s'", self.container.name, cmd_line)
        exec_result: ExecResult = self.container.exec_run(cmd_line, demux=True)

        return CommandResult(
            exec_result.exit_code, exec_result.output[0], exec_result.output[1]
        )


T = TypeVar("T")


class DockerJSONCommandRunner(DockerCommandRunner):
    """Extension of `DockerCommandRunner` which adds `--json` flag to command args."""

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
