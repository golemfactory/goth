"""Implementation of `yagna payment` subcommands"""

from typing import NamedTuple

from .base import make_args
from .typing import CommandRunner


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
        self: CommandRunner,
        requestor_mode: bool = False,
        provider_mode: bool = False,
        data_dir: str = "",
        address: str = "",
    ) -> str:
        """Run `<cmd> payment init` with optional extra args.
        Return the command's output.
        """

        args = make_args("payment", "init", address, data_dir=data_dir)
        if requestor_mode:
            args.append("-r")
        if provider_mode:
            args.append("-p")
        return self.run_command(*args)

    def payment_status(
        self: CommandRunner, data_dir: str = "", address: str = ""
    ) -> PaymentStatus:
        """Run `<cmd> payment status` with optional extra args.
        Parse the command's output as a `PatmentStatus` and return it.
        """

        args = make_args("payment", "status", address, data_dir=data_dir)
        output = self.run_json_command(*args)
        return PaymentStatus(
            amount=float(output["amount"]),
            incoming=Payments(
                **{key: float(value) for key, value in output["incoming"].items()}
            ),
            outgoing=Payments(
                **{key: float(value) for key, value in output["outgoing"].items()}
            ),
            reserved=float(output["reserved"]),
        )
