"""Implementation of `yagna id` subcommands"""

from typing import NamedTuple, Optional, Sequence

from .base import DockerJSONCommandRunner, parse_json_table, unwrap_ok_err_json


class Identity(NamedTuple):
    """Stores information about an identity"""

    alias: Optional[str]
    is_default: bool
    is_locked: bool
    address: str


class YagnaIdMixin:
    """A mixin class that adds support for `<yagna-cmd> id` commands"""

    def id_create(
            self: DockerJSONCommandRunner,
            data_dir: str = "",
            alias: str = ""
    ) -> Identity:
        """Run `<yagna-cmd> id create` command."""

        args = ["id", "create", "--no-password"]
        if data_dir:
            args.extend(["-d", data_dir])
        if alias:
            args.append(alias)
        output = self.run_json_command(*args)
        result = unwrap_ok_err_json(output)
        return Identity(
            result["alias"],
            result["isDefault"],
            result["isLocked"],
            result["nodeId"]
        )

    def id_show(
            self: DockerJSONCommandRunner,
            data_dir: str = "",
            alias: str = ""
    ) -> Optional[Identity]:
        """Return the output of `<yagna-cmd> id show`."""

        args = ["id", "show"]
        if data_dir:
            args.extend(["-d", data_dir])
        if alias:
            args.append(alias)
        output = self.run_json_command(*args)
        result = unwrap_ok_err_json(output)
        if result is not None:
            return Identity(
                result["alias"],
                result["isDefault"],
                result["isLocked"],
                result["nodeId"]
            )
        return None

    def id_list(
            self: DockerJSONCommandRunner,
            data_dir: str = ""
    ) -> Sequence[Identity]:
        """Return the output of `<yagna-cmd> id list`."""

        args = ["id", "list"]
        if data_dir:
            args.extend(["-d", data_dir])
        output = self.run_json_command(*args)
        return [
            Identity(
                r["alias"],
                r["default"] == "X",
                r["locked"] == "X",
                r["address"]
            )
            for r in parse_json_table(output)
        ]
