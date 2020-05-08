"""Implementation of `yagna app-key` subcommands"""

from typing import NamedTuple, Sequence

from .base import DockerJSONCommandRunner, parse_json_table


class AppKeyInfo(NamedTuple):
    """Information about an application key"""

    name: str
    key: str
    id: str
    role: str
    created: str


class YagnaAppKeyMixin:
    """A mixin class that adds support for `<yagna-cmd> app-key` commands"""

    def app_key_create(
            self: DockerJSONCommandRunner,
            name: str,
            role: str = "",
            identity: str = "",
            data_dir: str = ""
    ) -> str:
        """"Run `<cmd> app-key create <name>` with optional extra args.
        Return the application key parsed from the command's output.
        """

        args = ["app-key", "create", name]
        if role:
            args.extend(["--role", role])
        if identity:
            args.extend(["--id", identity])
        if data_dir:
            args.extend(["-d", data_dir])
        output = self.run_json_command(*args)
        assert isinstance(output, str)
        return output

    def app_key_drop(
            self: DockerJSONCommandRunner,
            name: str,
            identity: str = "",
            data_dir: str = ""
    ) -> str:
        """Run `<cmd> app-key drop <name>` with optional extra args.
        Return the command's output.
        """

        args = ["app-key", "drop", name]
        if identity:
            args.extend(["--id", identity])
        if data_dir:
            args.extend(["-d", data_dir])
        return self.run_command(*args)

    def app_key_list(
            self: DockerJSONCommandRunner,
            identity: str = "",
            data_dir: str = ""
    ) -> Sequence[AppKeyInfo]:
        """Run `<cmd> app-key list` with optional extra args.
        Return the list of `AppKeyInfo`s parsed from the command's output.
        """

        args = ["app-key", "list"]
        if identity:
            args.extend(["--id", identity])
        if data_dir:
            args.extend(["-d", data_dir])
        output = self.run_json_command(*args)
        return [
            AppKeyInfo(**info)
            for info in parse_json_table(output)
        ]
