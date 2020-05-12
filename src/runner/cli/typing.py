"""Type definitions for type-checking mixin classes with mypy (and no other purpose)"""

from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:

    from typing_extensions import Protocol
    from docker.models.containers import ExecResult

    class CommandRunner(Protocol):
        """A protocol used for type annotations of self in mixin classes"""

        def run_command(self, *cmd_args: str) -> str:
            """Run the command with `cmd_args`, raise exception on error."""

        def run_command_no_throw(self, *cmd_args: str) -> ExecResult:
            """Run the command with `cmd_args`, don't raise exceptions."""

        def run_json_command(self, *cmd_args: str) -> Any:
            """Run the command with `--json` flag."""


else:
    CommandRunner = object
