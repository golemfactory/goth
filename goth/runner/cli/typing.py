"""Type definitions for type-checking mixin classes with mypy (and no other purpose)."""

from typing import TYPE_CHECKING


if TYPE_CHECKING:

    from typing import Tuple, Type, TypeVar

    from typing_extensions import Protocol
    from docker.models.containers import ExecResult

    V = TypeVar("V")

    class CommandRunner(Protocol):
        """A protocol used for type annotations of self in mixin classes."""

        def run_command(self, *cmd_args: str) -> Tuple[str, str]:
            """Run the command with `cmd_args`, raise exception on error."""

        def run_command_no_throw(self, *cmd_args: str) -> ExecResult:
            """Run the command with `cmd_args`, don't raise exceptions."""

        def run_json_command(self, ty: Type[V], *cmd_args: str) -> V:
            """Run the command with `--json` flag."""


else:
    CommandRunner = object
