"""
Utility classes for executing yagna commands inside a Docker container.

The approach taken here is that it is more common to expect successful command
execution and treat errors as exceptions (even in tests), and hence instead
of returning `ExecResult` values from which the output/error must be unwrapped,
output of successful commands is returned directly and `CommandError`
exceptions are raised on errors.
"""
import json
import logging
from typing import Any, List, Optional, Mapping, NamedTuple, Sequence, Tuple

from docker.models.containers import Container, ExecResult
from typing_extensions import TypedDict

from src.runner.exceptions import CommandError


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _parse_json_table(output_dict: dict) -> List[dict]:
    headers: Optional[list] = output_dict.get("headers")
    values: Optional[list] = output_dict.get("values")

    if not headers or not values:
        return []

    result = []
    row: Tuple[str]
    for row in values:
        row_dict = {}
        for i, key in enumerate(headers):
            row_dict[key] = row[i]
        result.append(row_dict)

    return result


def _unwrap_ok_err_json(output_dict: dict) -> dict:
    if "Ok" in output_dict:
        return output_dict["Ok"]
    if "Err" in output_dict:
        raise CommandError(json.dumps(output_dict["Err"]))
    raise ValueError(json.dumps(output_dict))


class CliWrapper:
    """
    Wrapper for executing commands in a running docker container
    
    """

    def __init__(self, container: Container, command: str):
        self.container = container
        self.command = command

    def run_command(self, *cmd_args, **kwargs) -> str:
        """Run command with `cmd_args`, return its output on success, 
        raise `CommandError` on error
        """
        result = self.run_command_no_throw(*cmd_args, **kwargs)
        if result.exit_code != 0:
            raise CommandError(result.output.decode())
        return result.output

    def run_command_no_throw(self, *cmd_args, **kwargs) -> ExecResult:
        """Run command with `cmd_args`"""
        cmd_line = f"{self.command} {' '.join(cmd_args)}"
        logger.debug("[%s] command: '%s'", self.container.name, cmd_line)
        return self.container.exec_run(cmd_line, **kwargs)


class Identity(NamedTuple):
    """Stores information about an identity"""
    alias: Optional[str]
    is_default: bool
    is_locked: bool
    address: str


class Payments(NamedTuple):
    accepted: float
    confirmed: float
    rejected: float
    requested: float


class PaymentStatus(NamedTuple):
    """Information about payment status"""
    amount: float
    incoming: Payments
    outgoing: Payments
    reserved: float


class YagnaCli(CliWrapper):
    """Wrapper for running `yagna ...` commands"""

    def __init__(self, container: Container):
        super().__init__(container, "yagna")

    # `yagna id` subcommand

    def id_create(self, data_dir: str = "", alias: str = "") -> Identity:
        args = ["id", "create", "--no-password"]
        if data_dir:
            args.extend(["-d", data_dir])
        if alias:
            args.append(alias)
        output = self._run_json_cmd(*args)
        result = _unwrap_ok_err_json(output)
        return Identity(
            result["alias"],
            result["isDefault"],
            result["isLocked"],
            result["nodeId"]
        )

    def id_show(self, data_dir: str = "", alias: str = "") -> Identity:
        """Return the output of `yagna id show`"""
        args = ["id", "show"]
        if data_dir:
            args.extend(["-d", data_dir])
        if alias:
            args.append(alias)
        output = self._run_json_cmd(*args)
        result = _unwrap_ok_err_json(output)
        return Identity(
            result["alias"],
            result["isDefault"],
            result["isLocked"],
            result["nodeId"]
        )

    def id_list(self, data_dir: str = "") -> Sequence[Identity]:
        """Return the output of `yagna id list`"""
        args = ["id", "list"]
        if data_dir:
            args.extend(["-d", data_dir])
        output = self._run_json_cmd(*args)
        return [
            Identity(
                r["alias"], 
                r["default"] == "X", 
                r["locked"] == "X", 
                r["address"]
            )
            for r in _parse_json_table(output)    
        ]

    # `yagna app-key` subcommand
    def app_key_create(
        self,
        name: str,
        role: str = "",
        identity: str = "",
        data_dir: str = ""
    ) -> str:
        """Create an app-key with given name"""
        args = ["app-key", "create", name]
        if role:
            args.extend(["--role", role])
        if identity:
            args.extend(["--id", identity])
        if data_dir:
            args.extend(["--data_dir", data_dir])
        output = self._run_json_cmd(*args)
        assert isinstance(output, str)
        return output


    # `yagna payment` subcommand

    def payment_init(
        self,
        requestor_mode: bool = False,
        provider_mode: bool = False,
        data_dir: str = "",
        identity: str = "",
    ) -> str:
        """Run `yagna payment init`, return the command's output"""
        args = ["payment", "init"]
        if requestor_mode:
            args.append("-r")
        if provider_mode:
            args.append("-p")
        if data_dir:
            args.extend(["-d", data_dir])
        if identity:
            args.append(identity)
        return self.run_command(*args)

    def payment_status(
        self, 
        data_dir: str = "",
        identity: str = ""
    ) -> PaymentStatus:
        args = ["payment", "status"]
        if data_dir:
            args.extend(["-d", data_dir])
        if identity:
            args.append(identity)
        output = self._run_json_cmd(*args)    
        return PaymentStatus(
            amount=float(output["amount"]),
            incoming=Payments(**{
                    key: float(value) 
                    for key, value in output["incoming"].items()
                }
            ),
            outgoing=Payments(**{
                    key: float(value)
                    for key, value in output["outgoing"].items()
                }
            ),
            reserved=float(output["reserved"])
        )

    # legacy methods

    def get_app_keys(self):
        result = self._run_json_cmd("app-key", "list")
        return _parse_json_table(json.loads(result.output))

    def create_app_key(self, key_name: str) -> str:
        result = self._run_json_cmd("app-key", "create", key_name)
        return json.loads(result.output)

    def _run_json_cmd(self, *args) -> Any:
        if "--json" not in args:
            args = args + ("--json",)
        output = self.run_command(*args)
        return json.loads(output)


class YaProviderCli(CliWrapper):
    """Wrapper for running `ya-provider ...` commands"""

    def __init__(self, container: Container):
        super().__init__(container, "ya-provider")



if __name__ == "__main__":

    import docker
    import time

    client = docker.from_env()
    yagna_container = client.containers.run(
        "yagna", entrypoint=["yagna", "service", "run", "-d", "/"], detach=True
    )
    try:
        while yagna_container.status != "running":
            print("Waiting for the container...")
            time.sleep(1)
            yagna_container.reload()

        cli = YagnaCli(yagna_container)

        # id create

        # default call
        id = cli.id_create()
        assert id.is_default is False
        assert id.alias is None
        addr1 = id.address
        print("Created ID:", addr1)

        # with alias
        id = cli.id_create(alias="id-alias")
        assert id.is_default is False
        assert id.alias == "id-alias"
        addr2 = id.address
        print("Created ID:", addr2)

        # the same alias again, should fail
        try:
            id = cli.id_create(alias="id-alias")
            assert False
        except CommandError as ce:
            print("Crreate ID failed:", ce)
            assert "UNIQUE constraint failed: identity.alias" in ce.args[0]
        
        # with a wrong data dir
        try:
            id = cli.id_create(data_dir="xyz")
            assert False
        except CommandError as ce:
            print("id create failed:", ce)
            assert 'data dir "xyz" does not exist' in ce.args[0]

        # id show

        # show default ID
        id = cli.id_show()
        assert id.is_default is True
        print("Default ID:", id.address)

        # show id by alias
        id = cli.id_show(alias=addr1)
        assert id.is_default is False
        assert id.alias is None
        assert id.address == addr1

        id = cli.id_show(alias="id-alias")
        assert id.is_default is False
        assert id.alias == "id-alias"
        assert id.address == addr2

        # nonexistent alias
        # res = cli.id_show(alias="unknown")
 
        # wrong data dir
        try:
            id = cli.id_show(data_dir="xyz")
            assert False
        except CommandError as ce:
            print("id show failed:", ce)
            assert 'data dir "xyz" does not exist' in ce.args[0]

        # id list
        ids = cli.id_list()
        print("id list:", ids)
        assert any(id.is_default is True for id in ids)

        # app-key create
        key1 = cli.app_key_create("key1")
        print("new app-key:", key1)

        key2 = cli.app_key_create("key2")
        print("new app-key:", key2)
        assert key1 != key2


        # payment init

        # res = cli.payment_init()

        # res = cli.payment_init(provider_mode=True)

        # res = cli.payment_init(requestor_mode=True)

        # res = cli.payment_init(provider_mode=True, requestor_mode=True)
        
        try:
            res = cli.payment_init(identity="fake")
            assert False
        except CommandError as ce:
            print("payment init failed:", ce)
            assert "NodeId parsing error" in ce.args[0]

        try:
            fake_id = "0x0123456789012345678901234567890123456789"
            res = cli.payment_init(requestor_mode=True, identity=fake_id)
            assert False
        except CommandError as ce:
            print("payment init failed:", ce)

        try:
            res = cli.payment_init(data_dir="xyz")
            assert False
        except CommandError as ce:
            print("payment init failed:", ce)
            assert 'data dir "xyz" does not exist' in ce.args[0]
        
        # payment status
        status = cli.payment_status()
        print("Payment status:", status)
        assert status.incoming.accepted == 0.0
        assert status.outgoing.rejected == 0.0

        try:
            status = cli.payment_status(identity="fake")
            assert False
        except CommandError as ce:
            print("payment status failed:", ce)
            assert "NodeId parsing error" in ce.args[0]

        fake_id = "0x0123456789012345678901234567890123456789"
        status = cli.payment_status(identity=fake_id)

        try:
            status = cli.payment_status(data_dir="xyz")
            assert False
        except CommandError as ce:
            print("payment status failed:", ce)
            assert 'data dir "xyz" does not exist' in ce.args[0]



        """
                 
        cli.create_app_key("test-key")
        app_keys = cli.get_app_keys()
        print("App keys:", app_keys)

        exec_result = cli.payment_init(identity=node_id)
        print("Payment init, exit code:", exec_result.exit_code)
        """

    finally:
        yagna_container.stop()
        yagna_container.remove()
        # yagna_container.reload()
        # print("Container removed, status:", yagna_container.status)
