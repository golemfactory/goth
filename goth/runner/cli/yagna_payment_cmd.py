"""Implementation of `yagna payment` subcommands."""

from dataclasses import dataclass
from typing import Dict

from goth.runner.cli.base import make_args
from goth.runner.cli.typing import CommandRunner


@dataclass(frozen=True)
class Payments:
    """Information about payment amounts."""

    accepted: float
    confirmed: float
    rejected: float
    requested: float


@dataclass(frozen=True)
class PaymentStatus:
    """Information about payment status."""

    amount: float
    incoming: Payments
    outgoing: Payments
    reserved: float


class YagnaPaymentMixin:
    """A mixin class that adds support for `<yagna-cmd> payment` commands."""

    def payment_init(
        self: CommandRunner,
        requestor_mode: bool = False,
        provider_mode: bool = False,
        data_dir: str = "",
        payment_driver: str = "ngnt",
        address: str = "",
    ) -> str:
        """Run `<cmd> payment init` with optional extra args.

        Return the command's output.
        """

        args = make_args("payment", "init", payment_driver, address, data_dir=data_dir)
        if requestor_mode:
            args.append("-r")
        if provider_mode:
            args.append("-p")
        return self.run_command(*args)[0]

    def payment_status(
        self: CommandRunner, data_dir: str = "", driver: str = "ngnt"
    ) -> PaymentStatus:
        """Run `<cmd> payment status` with optional extra args.

        Parse the command's output as a `PatmentStatus` and return it.
        """

        args = make_args("payment", "status", driver, data_dir=data_dir)
        output = self.run_json_command(Dict, *args)
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
