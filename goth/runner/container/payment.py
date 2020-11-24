"""Module related to handling payment IDs in yagna containers."""

from dataclasses import dataclass
from enum import Enum, unique
import json
from pathlib import Path
from tempfile import gettempdir
from typing import Generator, List, NamedTuple
from uuid import uuid4

from goth.project import TEST_DIR

ENV_ACCOUNT_LIST = "ACCOUNT_LIST"

KEY_DIR = Path(TEST_DIR, "yagna", "keys")
TEMP_ID_DIR = Path(gettempdir(), "goth_payment_id")
TEMP_ID_DIR.mkdir(exist_ok=True)


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


@dataclass
class PaymentId:
    """Represents a single payment ID to be used with a yagna node.

    Consists of a list of payment accounts along with a common Ethereum key used by
    those accounts as their address.
    Supports dumping the accounts and key to temporary files to be used for mounting
    within a Docker container. For a given payment ID, its files share a common UUID
    in their names.
    """

    accounts: List[Account]
    key: EthKey

    _uuid: str = uuid4().hex

    @property
    def accounts_file(self) -> Path:
        """Return path to a file with a serialized version of this ID's accounts."""
        accounts_path = Path(TEMP_ID_DIR, f"accounts_{self._uuid}.json")

        if not accounts_path.exists():
            with accounts_path.open(mode="w+") as fd:
                json.dump(self.accounts, fd)

        return accounts_path

    @property
    def key_file(self) -> Path:
        """Return path to a file with a serialized version of this ID's Ethereum key."""
        key_path = Path(TEMP_ID_DIR, f"key_{self._uuid}.json")

        if not key_path.exists():
            with key_path.open(mode="w+") as fd:
                json.dump(self.key, fd)

        return key_path


class PaymentIdPool:
    """Class used for generating yagna payment IDs based on a pool of Ethereum keys.

    The pool of keys is loaded from key files stored in the repo under `KEY_DIR`.
    """

    _key_pool: Generator[EthKey, None, None]
    """Generator yielding pre-funded Ethereum keys loaded from a directory."""

    def __init__(self):
        self._key_pool = (self._key_from_file(f) for f in KEY_DIR.iterdir())

    def get_id(
        self,
        drivers: List[PaymentDriver] = [PaymentDriver.ngnt, PaymentDriver.zksync],
        receive: bool = True,
        send: bool = True,
    ) -> PaymentId:
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
        return PaymentId(account_list, key)

    def _get_key(self) -> EthKey:
        try:
            return next(self._key_pool)
        except StopIteration:
            raise KeyPoolDepletedError()

    def _key_from_file(self, path: Path) -> EthKey:
        with path.open() as fd:
            key_dict = json.load(fd)
            return EthKey(key_dict["address"], key_dict["crypto"])
