"""Implementation of `yagna app-key` subcommands"""

from typing import NamedTuple, Sequence

from .base import make_args, parse_json_table
from .typing import CommandRunner


class AppKeyInfo(NamedTuple):
    """Information about an application key"""

    name: str
    key: str
    address: str
    role: str
    created: str


class YagnaAppKeyMixin:
    """A mixin class that adds support for `<yagna-cmd> app-key` commands"""

    def app_key_create(
        self: CommandRunner,
        name: str,
        role: str = "",
        alias_or_addr: str = "",
        data_dir: str = "",
    ) -> str:
        """"Run `<cmd> app-key create <name>` with optional extra args.
        Return the application key parsed from the command's output.
        """

        args = make_args(
            "app-key", "create", name, role=role, id=alias_or_addr, data_dir=data_dir
        )
        output = self.run_json_command(*args)
        assert isinstance(output, str)
        return output

    def app_key_drop(
        self: CommandRunner, name: str, address: str = "", data_dir: str = "",
    ) -> str:
        """Run `<cmd> app-key drop <name>` with optional extra args.
        Return the command's output.
        """

        args = make_args("app-key", "drop", name, id=address, data_dir=data_dir)
        return self.run_command(*args)

    def app_key_list(
        self: CommandRunner, address: str = "", data_dir: str = ""
    ) -> Sequence[AppKeyInfo]:
        """Run `<cmd> app-key list` with optional extra args.
        Return the list of `AppKeyInfo`s parsed from the command's output.
        """

        args = make_args("app-key", "list", id=address, data_dir=data_dir)
        output = self.run_json_command(*args)
        return [
            AppKeyInfo(
                name=info["name"],
                key=info["key"],
                address=info["id"],
                role=info["role"],
                created=info["created"],
            )
            for info in parse_json_table(output)
        ]
