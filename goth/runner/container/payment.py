"""Module related to handling payment IDs in yagna containers."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
from tempfile import gettempdir
from typing import Iterator, List, Optional
from uuid import uuid4

from goth.project import DEFAULT_ASSETS_DIR
from goth.payment_config import PaymentConfig

ENV_ACCOUNT_LIST = "ACCOUNT_LIST"

DEFAULT_KEY_DIR = Path(DEFAULT_ASSETS_DIR / "keys")


def get_id_directory() -> Path:
    """Return temporary directory used for storing generated payment IDs."""
    temp_id_dir = Path(gettempdir(), "goth_payment_id")
    temp_id_dir.mkdir(exist_ok=True)
    return temp_id_dir


def clean_up() -> None:
    """Perform post-test cleanup related to payment IDs."""
    shutil.rmtree(get_id_directory(), ignore_errors=True)
    get_id_directory().mkdir(exist_ok=True)


class KeyPoolDepletedError(Exception):
    """Error raised when all pre-funded Ethereum keys have been assigned."""

    def __init__(self):
        super().__init__("No more pre-funded Ethereum keys available.")


@dataclass
class Account:
    """Data class representing a single yagna payment account."""

    address: str
    driver: str
    network: str
    token: str
    receive: bool = True
    send: bool = True


@dataclass
class EthKey:
    """Data class representing an Ethereum private key."""

    address: str
    crypto: dict
    id: str
    version: int


class PaymentId:
    """Represents a single payment ID to be used with a yagna node.

    Consists of a list of payment accounts along with a common Ethereum key used by
    those accounts as their address.
    Supports dumping the accounts and key to temporary files to be used for mounting
    within a Docker container. For a given payment ID, its files share a common UUID
    in their names.
    """

    accounts: List[Account]
    accounts_file: Path
    key: EthKey
    key_file: Path

    _uuid: str
    """UUID for this instance of `PaymentId`."""

    def __init__(self, accounts: List[Account], key: EthKey):
        self.accounts = accounts
        self.key = key
        self._uuid = uuid4().hex

        self.accounts_file = self._create_accounts_file()
        self.key_file = self._create_key_file()

    def _create_accounts_file(self) -> Path:
        accounts_path = Path(get_id_directory(), f"accounts_{self._uuid}.json")
        with accounts_path.open(mode="w+") as fd:
            serializable = [asdict(a) for a in self.accounts]
            json.dump(serializable, fd)
        return accounts_path

    def _create_key_file(self) -> Path:
        key_path = Path(get_id_directory(), f"key_{self._uuid}.json")
        with key_path.open(mode="w+") as fd:
            json.dump(asdict(self.key), fd)
        return key_path


class PaymentIdPool:
    """Class used for generating yagna payment IDs based on a pool of Ethereum keys.

    The pool of keys is loaded from key files stored in the repo under a given dir
    (`DEFAULT_KEY_DIR` by default).
    """

    _key_pool: Iterator[EthKey]
    """Iterator yielding pre-funded Ethereum keys loaded from a directory."""

    def __init__(self, key_dir: Optional[Path] = None):
        key_dir = key_dir or DEFAULT_KEY_DIR
        self._key_pool = (self._key_from_file(f) for f in key_dir.iterdir())

    def get_id(
        self,
        payment_config: PaymentConfig,
        receive: bool = True,
        send: bool = True,
    ) -> PaymentId:
        """Generate payment accounts with a common, pre-funded Ethereum key.

        Attempts to obtain a key from the pool and, if available, creates a list of
        payment accounts based on the provided parameters.
        Only a single account is created, for payment_config.driver.
        The parameters `receive` and `send` are shared between the accounts.
        Once the key pool is depleted, attempting to get another account results in
        `KeyPoolDepletedError` being raised.
        """
        key = self._get_key()
        account = Account(
            address=f"0x{key.address}",
            driver=payment_config.driver,
            network=payment_config.network,
            token=payment_config.token,
            receive=receive,
            send=send,
        )
        return PaymentId([account], key)

    def _get_key(self) -> EthKey:
        try:
            return next(self._key_pool)
        except StopIteration:
            raise KeyPoolDepletedError()

    def _key_from_file(self, path: Path) -> EthKey:
        with path.open() as fd:
            key_dict = json.load(fd)
            return EthKey(**key_dict)
