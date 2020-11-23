"""Module related to handling payment IDs in yagna containers."""

from enum import Enum, unique
import json
from pathlib import Path
from typing import Generator, List, NamedTuple, Tuple

from goth.project import TEST_DIR

KEY_DIR = Path(TEST_DIR, "yagna", "keys")


class KeyPoolDepletedError(Exception):
    """Error raised when all pre-funded Ethereum keys have been assigned."""

    def __init__(self):
        super().__init__("No more pre-funded Ethereum keys available.")


@unique
# https://docs.python.org/3/library/enum.html#restricted-enum-subclassing
class PaymentDriver(str, Enum):
    """Enum listing the payment drivers that can be used with yagna."""

    ngnt = "ngnt"
    zksync = "zksync"


class Account(NamedTuple):
    """Named tuple representing a single yagna payment account."""

    address: str
    driver: PaymentDriver = PaymentDriver.zksync
    receive: bool = True
    send: bool = True


class EthKey(NamedTuple):
    """Named tuple representing an Ethereum private key."""

    address: str
    crypto: dict


class PaymentIdPool:
    """Class used for generating yagna accounts based on a pool of Ethereum keys.

    The pool of keys is loaded from key files stored in the repo under `KEY_DIR`.
    """

    _key_pool: Generator[EthKey, None, None]

    def __init__(self):
        # generator comprehension yielding eth keys loaded from files
        self._key_pool = (self._key_from_file(f) for f in KEY_DIR.iterdir())

    def get_accounts(
        self,
        drivers: List[PaymentDriver] = [PaymentDriver.zksync],
        receive: bool = True,
        send: bool = True,
    ) -> Tuple[EthKey, List[Account]]:
        """Generate payment accounts with a common, pre-funded Ethereum key.

        Attempts to obtain a key from the pool and, if available, creates a list of
        payment accounts based on the provided parameters.
        For each payment driver specified, a separate account is generated.
        The parameters `receive` and `send` are shared between the accounts.
        Once the key pool is depleted, attempting to get another account results in
        `KeyPoolDepletedError` being raised.
        """
        key = self._get_key()
        account_list = [
            Account(
                address=key.address,
                driver=driver,
                receive=receive,
                send=send,
            )
            for driver in drivers
        ]
        return key, account_list

    def _get_key(self) -> EthKey:
        try:
            return next(self._key_pool)
        except StopIteration:
            raise KeyPoolDepletedError()

    def _key_from_file(self, path: Path) -> EthKey:
        with path.open() as fd:
            key_dict = json.load(fd)
            return EthKey(key_dict["address"], key_dict["crypto"])
