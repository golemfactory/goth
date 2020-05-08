"""Implementation of `yagna payment` subcommands"""

from typing import NamedTuple

from .base import DockerJSONCommandRunner


class Payments(NamedTuple):
    """Information about payment amounts"""

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


class YagnaPaymentMixin:
    """A mixin class that adds support for `<yagna-cmd> payment` commands"""

    def payment_init(
            self: DockerJSONCommandRunner,
            requestor_mode: bool = False,
            provider_mode: bool = False,
            data_dir: str = "",
            identity: str = "",
    ) -> str:
        """Run `<cmd> payment init` with optional extra args.
        Return the command's output.
        """

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
            self: DockerJSONCommandRunner,
            data_dir: str = "",
            identity: str = ""
    ) -> PaymentStatus:
        """Run `<cmd> payment status` with optional extra args.
        Parse the command's output as a `PatmentStatus` and return it.
        """

        args = ["payment", "status"]
        if data_dir:
            args.extend(["-d", data_dir])
        if identity:
            args.append(identity)
        output = self.run_json_command(*args)
        return PaymentStatus(
            amount=float(output["amount"]),
            incoming=Payments(**{
                key: float(value)
                for key, value in output["incoming"].items()
            }),
            outgoing=Payments(**{
                key: float(value)
                for key, value in output["outgoing"].items()
            }),
            reserved=float(output["reserved"])
        )
