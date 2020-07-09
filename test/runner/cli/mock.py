"""Utils for mocking CLI components."""

from dataclasses import asdict, astuple
import ipaddress
import json
import random
import re
import shlex
import socket
import struct
import subprocess
from typing import List

from unittest.mock import MagicMock

from goth.runner.cli.yagna_app_key_cmd import AppKeyInfo
from goth.runner.cli.yagna_id_cmd import Identity
from goth.runner.cli.yagna_payment_cmd import Payments, PaymentStatus
from goth.runner.exceptions import CommandError, KeyAlreadyExistsError


class MockYagnaCLI:
    """Mocked Yagna CLI."""

    commands: dict = {}
    id_list = {"headers": ["alias", "default", "locked", "address"], "values": []}
    id_values: List[Identity]
    key_list = {"headers": ["name", "key", "id", "role", "created"], "values": []}
    key_values: List[AppKeyInfo]
    payment_status_value = PaymentStatus(
        0, Payments(0, 0, 0, 0), Payments(0, 0, 0, 0), 0
    )

    def __init__(self):
        """Create a MockYagnaCLI."""

        """
            Commands are mapped as an object, so each command can
            point its relevant function to call. This is done automatically
            by call_fn method under MockYagnaCLI.

            To add more commands, simply map the command as other commands in object
            and pass the function to be executed as a value.
        """
        self.commands = {
            "/bin/sh": {"-c": self.echo_demux},
            "yagna": {
                "app-key": {"create": self.create_app_key, "list": self.list_app_key},
                "id": {
                    "create": self.create_id,
                    "show": self.show_id,
                    "list": self.list_id,
                },
                "payment": {"init": self.payment_status, "status": self.payment_status},
            },
        }
        self.id_values = [
            Identity(alias="", is_default=True, is_locked=False, address="")
        ]
        self.key_values = []

    def is_ipv4(self, value):
        """Check if given value is IPv4."""
        try:
            ipaddress.IPv4Network(value)
            return True
        except ValueError:
            return False

    def deep_get_fn(self, dictionary, keys):
        """Recursively search for function in nested object."""
        if not keys or dictionary is None:
            return dictionary

        if callable(dictionary):
            return dictionary

        return self.deep_get_fn(dictionary.get(keys[0]), keys[1:])

    def call_fn(self, args, cmd, options):
        """Call mapped function from given commands."""
        fn = self.deep_get_fn(self.commands, args)
        return fn(options, cmd)

    def parse_options(self, cmd_args):
        """Parse flags from given commands."""
        cmd_options = {}

        """
            Create key value pairs to catch flags and their values

            i.e.
            input: "yagna id create --no-password id-alias"
            output: {('id-alias', '--'), ('id', 'create'),
            ('create', '--no-password'),
            ('--no-password', 'id-alias'), ('yagna', 'id')}
        """
        zip_pairs = zip(cmd_args, cmd_args[1:] + ["--"])
        for key, value in zip_pairs:
            if key.startswith("--"):
                cmd_options[key] = True if value.startswith("-") else value
        return cmd_options

    def exec_run(self, cmd, **kwargs):
        """Mock function of docker exec_run."""
        cmd = cmd.replace("--json", "")
        cmd_args = shlex.split(cmd)
        cmd_options = self.parse_options(cmd_args)

        result_mock = MagicMock()
        result_mock.exit_code = 0

        result_mock.output = self.call_fn(cmd_args, cmd, cmd_options)
        return result_mock

    def echo_demux(self, _options, cmd):
        """Mock function of command line interface of yagna docker container."""
        command = re.search(r"\'(.*?)\'", cmd).group(1)
        proc = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        proc.wait()
        result = proc.communicate()
        if proc.returncode != 0:
            raise CommandError(
                "no-such-command"
            )  # test_error_output_demultiplexing is depend on given message

        return result

    def create_app_key(self, options, cmd):
        """Create yagna app key."""
        alias = options.get("--id")
        key = re.search(r"^.*?\bcreate \'(.*)\'(?:.+)?$", cmd).group(1)

        if isinstance(alias, str) and not [
            value for value in self.id_values if alias == value.alias
        ]:
            raise CommandError("Given alias is not on the list")

        if [value for value in self.key_values if key == value.key]:
            raise KeyAlreadyExistsError(key)

        self.key_values.append(AppKeyInfo("name", key, alias, "", ""))
        key = f'"{key}"'
        return (key.encode(), b"")

    def list_app_key(self, options, cmd):
        """List current yagna app keys."""
        key_id = options.get("--id")
        alias = None

        if self.is_ipv4(key_id):
            result_alias = [
                value for value in self.id_values if value.address == key_id
            ]
            alias = result_alias[0].alias
            alias = alias if alias else key_id
        else:
            alias = key_id

        key_value_list = (
            [value for value in self.key_values if value.address == alias]
            if key_id
            else self.key_values
        )
        self.key_list["values"] = [
            list(asdict(value).values()) for value in key_value_list
        ]
        return (json.dumps(self.key_list).encode("utf-8"), b"")

    def create_id(self, options, cmd):
        """Create id."""
        alias = options.get("--no-password")
        alias = alias if isinstance(alias, str) else None

        if alias and [value for value in self.id_values if alias == value.alias]:
            raise CommandError("Given alias is already on the list")

        address = socket.inet_ntoa(struct.pack(">I", random.randint(1, 0xFFFFFFFF)))
        self.id_values.append(Identity(alias, False, False, address))
        result = {
            "Ok": {
                "alias": alias,
                "isDefault": False,
                "isLocked": False,
                "nodeId": address,
            }
        }
        return (json.dumps(result).encode("utf-8"), b"")

    def show_id(self, _options, cmd):
        """Show specific id if exist."""
        filter_key = "address"
        result_list = self.id_values
        alias_or_addr = None
        match = re.search(r"^.*?\bshow ([^\s]+)", cmd)
        if match:
            alias_or_addr = match.group(1)

        if alias_or_addr:
            if not self.is_ipv4(alias_or_addr):
                filter_key = "alias"
            result_list = [
                value
                for value in self.id_values
                if getattr(value, filter_key) == alias_or_addr
            ]
        if len(result_list) < 1:
            result = {"Ok": None}
        else:
            [alias, is_default, is_locked, address] = astuple(result_list[0])
            result = {
                "Ok": {
                    "alias": alias,
                    "isDefault": is_default,
                    "isLocked": is_locked,
                    "nodeId": address,
                }
            }
        return (json.dumps(result).encode("utf-8"), b"")

    def list_id(self, _options, _cmd):
        """List current ids."""
        list_values = []
        for value in self.id_values:
            identity_as_list = list(asdict(value).values())
            identity_as_list[1] = "X" if value.is_default else None
            list_values.append(identity_as_list)

        self.id_list["values"] = list_values
        return (json.dumps(self.id_list).encode("utf-8"), b"")

    def payment_status(self, _options, _cmd):
        """Show payment statuses."""
        return (json.dumps(asdict(self.payment_status_value)).encode("utf-8"), b"")
