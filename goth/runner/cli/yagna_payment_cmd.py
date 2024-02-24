"""Implementation of `yagna payment` subcommands."""

from dataclasses import dataclass
from typing import Dict, Optional

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

    @staticmethod
    def from_dict(source: dict) -> "PaymentStatus":
        """Parse a dict into an instance of `PaymentStatus`."""
        return PaymentStatus(
            amount=float(source["amount"]),
            incoming=Payments(**{key: float(value) for key, value in source["incoming"].items()}),
            outgoing=Payments(**{key: float(value) for key, value in source["outgoing"].items()}),
            reserved=float(source["reserved"]),
        )


@dataclass(frozen=True)
class Network:
    """Contains information about `Network`."""

    default_token: str
    tokens: Dict[str, str]


@dataclass(frozen=True)
class Driver:
    """Contains driver details fields."""

    default_network: str
    networks: Dict[str, Network]

    @staticmethod
    def from_dict(source: dict):
        """Parse a dict into an instance of `Driver` class."""
        return Driver(
            default_network=source["default_network"],
            networks={key: Network(**val) for key, val in source["networks"].items()},
        )


class YagnaPaymentMixin:
    """A mixin class that adds support for `<yagna-cmd> payment` commands."""

    def payment_fund(self: CommandRunner, payment_driver: str) -> None:
        """Run `<cmd> payment fund` with optional extra args."""
        args = make_args("payment", "fund", driver=payment_driver)
        self.run_command(*args)

    def payment_init(
        self: CommandRunner,
        payment_driver: str,
        sender_mode: bool = False,
        receiver_mode: bool = False,
        data_dir: str = "",
        address: Optional[str] = None,
        network: Optional[str] = None,
    ) -> None:
        """Run `<cmd> payment init` with optional extra args.

        Return the command's output.
        """

        args = make_args(
            "payment",
            "init",
            data_dir=data_dir,
            driver=payment_driver,
            address=address,
            network=network,
        )
        if sender_mode:
            args.append("--sender")
        if receiver_mode:
            args.append("--receiver")

        self.run_command(*args)[0]

    def payment_status(
        self: CommandRunner,
        driver: str,
        data_dir: str = "",
    ) -> PaymentStatus:
        """Run `<cmd> payment status` with optional extra args.

        Parse the command's output as a `PaymentStatus` and return it.
        """

        args = make_args("payment", "status", driver, data_dir=data_dir)
        output = self.run_json_command(Dict, *args)
        return PaymentStatus.from_dict(output)

    def payment_drivers(
        self: CommandRunner,
    ) -> Dict[str, Driver]:
        """Run `<cmd> payment drivers` without any extra args.

        Parse the command's output as a `Dict[str, Driver]` and return it.
        """

        args = make_args("payment", "driver", "list")
        output = self.run_json_command(Dict, *args)
        return {key: Driver.from_dict(val) for key, val in output.items()}

    def payment_release_allocations(self: CommandRunner) -> None:
        """Run `<cmd> payment release-allocations` without any extra args."""

        args = make_args("payment", "release-allocations")
        self.run_command(*args)
