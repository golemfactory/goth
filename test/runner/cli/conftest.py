"""Code common for all pytest modules in this package"""
from unittest.mock import MagicMock

from docker import DockerClient
from docker.models.containers import Container
import json
import ipaddress
import pytest
import re
import random
import shlex
import socket
import struct
import subprocess

from src.runner.container import DockerContainer
from src.runner.container.yagna import YagnaContainer, YagnaContainerConfig
from src.runner.exceptions import CommandError, KeyAlreadyExistsError
from src.runner.log import LogConfig
from src.runner.probe import Role

GENERIC_COMMAND = ["cmd_name", "-f", "flag_value"]
GENERIC_ENTRYPOINT = "/usr/bin/binary_name"
GENERIC_IMAGE = "some_docker_image"
GENERIC_NAME = "generic_container"
YAGNA_CONTAINER_NAME = "yagna_container"

key_list = {"headers": ["name", "key", "id", "role", "created"], "values": []}

key_values = []

id_list = {"headers": ["alias", "default", "locked", "address"], "values": []}

id_values = []

payment_status_value = {
    "amount": 0,
    "incoming": {"accepted": 0, "confirmed": 0, "rejected": 0, "requested": 0},
    "outgoing": {"accepted": 0, "confirmed": 0, "rejected": 0, "requested": 0},
    "reserved": 0,
}


def echo_demux(_options, cmd):
    command = re.search(r"\'(.*?)\'", cmd).group(1)
    proc = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    proc.wait()
    result = proc.communicate()
    if proc.returncode != 0:
        raise CommandError("no-such-command")

    return result


def create_app_key(options, cmd):
    alias = options.get("--id")
    key = re.search(r"^.*?\bcreate \'(.*)\'(?:.+)?$", cmd).group(1)

    if isinstance(alias, str) and not is_item_in(id_values, alias, 0):
        raise CommandError("no-such-command")

    if is_item_in(key_values, key, 1):
        raise KeyAlreadyExistsError(key)

    key_values.append(["name", key, alias, "", ""])
    key = f'"{key}"'
    return (key.encode(), b"")


def list_app_key(options, cmd):
    key_id = options.get("--id")
    alias = None

    if is_ipv4(key_id):
        result_alias = filter_list(id_values, key_id, 3)
        alias = result_alias[0][0]
        alias = alias if alias else key_id
    else:
        alias = key_id

    key_value_list = filter_list(key_values, alias, 2) if key_id else key_values
    key_list["values"] = key_value_list
    return (json.dumps(key_list).encode("utf-8"), b"")


def create_id(options, cmd):
    alias = options.get("--no-password")
    alias = alias if isinstance(alias, str) else None

    if alias and is_item_in(id_values, alias, 0):
        raise CommandError("no-such-command")

    address = socket.inet_ntoa(struct.pack(">I", random.randint(1, 0xFFFFFFFF)))
    id_values.append([alias, None, False, address])
    result = {
        "Ok": {
            "alias": alias,
            "isDefault": False,
            "isLocked": False,
            "nodeId": address,
        }
    }
    return (json.dumps(result).encode("utf-8"), b"")


def show_id(_options, cmd):
    alias_or_addr = None
    filter_index = 3
    result_list = id_values
    try:
        alias_or_addr = re.search(r"^.*?\bshow ([^\s]+)", cmd).group(1)
    except:
        alias_or_addr = None

    if alias_or_addr:
        if not is_ipv4(alias_or_addr):
            filter_index = 0
        result_list = filter_list(id_values, alias_or_addr, filter_index)

    if len(result_list) < 1:
        result = {"Ok": None}
    else:
        [alias, is_default, is_locked, address] = result_list[0]
        result = {
            "Ok": {
                "alias": alias,
                "isDefault": True if is_default == "X" else False,
                "isLocked": is_locked,
                "nodeId": address,
            }
        }
    return (json.dumps(result).encode("utf-8"), b"")


def list_id(_options, _cmd):
    id_list["values"] = id_values
    return (json.dumps(id_list).encode("utf-8"), b"")


def payment_status(_options, _cmd):
    return (json.dumps(payment_status_value).encode("utf-8"), b"")


commands = {
    "/bin/sh": {"-c": echo_demux},
    "yagna": {
        "app-key": {"create": create_app_key, "list": list_app_key},
        "id": {"create": create_id, "show": show_id, "list": list_id},
        "payment": {"init": payment_status, "status": payment_status},
    },
}


def is_ipv4(value):
    try:
        ipaddress.IPv4Network(value)
        return True
    except ValueError:
        return False


def filter_list(target_list, item, index):
    return list(filter(lambda x: x[index] == item, target_list))


def is_item_in(target_list, item, index):
    result = filter_list(target_list, item, index)
    return len(result) > 0


def deep_get_fn(dictionary, keys):
    if not keys or dictionary is None:
        return dictionary

    if callable(dictionary):
        return dictionary

    return deep_get_fn(dictionary.get(keys[0]), keys[1:])


def call_fn(args, cmd, options):
    fn = deep_get_fn(commands, args)
    return fn(options, cmd)


def reset_states():
    key_values.clear()
    id_values.clear()
    id_values.append([None, "X", False, None])


@pytest.fixture
def exec_run():
    def _exec_run(cmd, demux):
        cmd = cmd.replace("--json", "")
        args = shlex.split(cmd)
        options = {
            k: True if v.startswith("-") else v
            for k, v in zip(args, args[1:] + ["--"])
            if k.startswith("-")
        }
        result_mock = MagicMock()
        result_mock.exit_code = 0

        result_mock.output = call_fn(args, cmd, options)
        return result_mock

    return _exec_run


@pytest.fixture
def mock_container(exec_run):
    mock_container = MagicMock(spec=Container)
    mock_container.status = "created"
    mock_container.exec_run = exec_run
    return mock_container


@pytest.fixture
def mock_docker_client(mock_container):
    client = MagicMock(spec=DockerClient)
    client.containers.create.return_value = mock_container
    return client


@pytest.fixture
def docker_container(mock_docker_client):
    mock_docker_client.containers.create.return_value = mock_container
    return DockerContainer(
        client=mock_docker_client,
        command=GENERIC_COMMAND,
        entrypoint=GENERIC_ENTRYPOINT,
        image=GENERIC_IMAGE,
        name=GENERIC_NAME,
    )


@pytest.fixture
def yagna_container(mock_docker_client):
    """A fixture for starting and terminating a container using the `yagna` image"""
    reset_states()
    config = MagicMock(spec=YagnaContainerConfig)
    config.name = YAGNA_CONTAINER_NAME
    config.environment = {}
    config.volumes = {}
    return YagnaContainer(mock_docker_client, config)
