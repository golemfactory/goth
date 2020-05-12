"""Implementation of `yagna id` subcommands"""

from typing import NamedTuple, Optional, Sequence

from .base import make_args, parse_json_table, unwrap_ok_err_json
from .typing import CommandRunner


class Identity(NamedTuple):
    """Stores information about an identity"""

    alias: Optional[str]
    is_default: bool
    is_locked: bool
    address: str


class YagnaIdMixin:
    """A mixin class that adds support for `<yagna-cmd> id` commands"""

    def id_create(self: CommandRunner, data_dir: str = "", alias: str = "") -> Identity:
        """Run `<yagna-cmd> id create` command."""

        args = make_args("id", "create", "--no-password", alias, data_dir=data_dir)
        output = self.run_json_command(*args)
        result = unwrap_ok_err_json(output)
        return Identity(
            result["alias"], result["isDefault"], result["isLocked"], result["nodeId"],
        )

    def id_show(
        self: CommandRunner, data_dir: str = "", alias_or_addr: str = ""
    ) -> Optional[Identity]:
        """Return the output of `<yagna-cmd> id show`."""

        args = make_args("id", "show", alias_or_addr, data_dir=data_dir)
        output = self.run_json_command(*args)
        result = unwrap_ok_err_json(output)
        if result is not None:
            return Identity(
                result["alias"],
                result["isDefault"],
                result["isLocked"],
                result["nodeId"],
            )
        return None

    def id_list(self: CommandRunner, data_dir: str = "") -> Sequence[Identity]:
        """Return the output of `<yagna-cmd> id list`."""

        args = make_args("id", "list", data_dir=data_dir)
        output = self.run_json_command(*args)
        return [
            Identity(r["alias"], r["default"] == "X", r["locked"] == "X", r["address"],)
            for r in parse_json_table(output)
        ]
