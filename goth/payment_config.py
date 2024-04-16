"""All possible payment-related configuration, in one place."""
from dataclasses import dataclass, field
from typing import Dict

GLM_CONTRACT_ADDRESS = "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34"
# Sets how many blocks need to be mined on the blockchain in order for a transaction
# to be considered confirmed. This is currently disabled due to ganache server not
# mining blocks automatically. See: https://github.com/golemfactory/gnt2/issues/172
REQUIRED_CONFIRMATIONS_COUNT = 0

_payment_config = {
    "erc20_mainnet": {
        "env": {
            "ERC20_MAINNET_REQUIRED_CONFIRMATIONS": REQUIRED_CONFIRMATIONS_COUNT,
            "MAINNET_GETH_ADDR": "http://ethereum-mainnet:8545",
            "MAINNET_MAX_FEE_PER_GAS": "1.0",
            "MAINNET_MULTI_PAYMENT_CONTRACT_ADDRESS": "0xFf807885934003A35b1284d7445fc83Fd23417e5",
            "MAINNET_LOCK_PAYMENT_CONTRACT_ADDRESS": "0xD756fb6A081CC11e7F513C39399DB296b1DE3036",
            "MAINNET_PRIORITY_FEE": "1.0",
            "MAINNET_GLM_CONTRACT_ADDRESS": GLM_CONTRACT_ADDRESS,
            "YA_PAYMENT_NETWORK": "mainnet",
        },
        "driver": "erc20",
        "network": "mainnet",
        "token": "GLM",
    },
    "erc20": {
        "env": {
            "ERC20_HOLESKY_REQUIRED_CONFIRMATIONS": REQUIRED_CONFIRMATIONS_COUNT,
            "HOLESKY_GETH_ADDR": "http://ethereum-holesky:8545",
            "HOLESKY_MAX_FEE_PER_GAS": "1.0",
            "HOLESKY_MULTI_PAYMENT_CONTRACT_ADDRESS": "0xFf807885934003A35b1284d7445fc83Fd23417e5",
            "HOLESKY_LOCK_PAYMENT_CONTRACT_ADDRESS": "0xD756fb6A081CC11e7F513C39399DB296b1DE3036",
            "HOLESKY_PRIORITY_FEE": "1.0",
            "HOLESKY_TGLM_CONTRACT_ADDRESS": GLM_CONTRACT_ADDRESS,
            "YA_PAYMENT_NETWORK": "holesky",
        },
        "driver": "erc20",
        "network": "holesky",
        "token": "tGLM",
    },
    "polygon": {
        "env": {
            "ERC20_POLYGON_REQUIRED_CONFIRMATIONS": REQUIRED_CONFIRMATIONS_COUNT,
            "POLYGON_GETH_ADDR": "http://ethereum-polygon:8545",
            "POLYGON_MAX_FEE_PER_GAS": "30.0",
            "POLYGON_MULTI_PAYMENT_CONTRACT_ADDRESS": "0xFf807885934003A35b1284d7445fc83Fd23417e5",
            "POLYGON_LOCK_PAYMENT_CONTRACT_ADDRESS": "0xD756fb6A081CC11e7F513C39399DB296b1DE3036",
            "POLYGON_PRIORITY_FEE": "30.0",
            "POLYGON_GLM_CONTRACT_ADDRESS": GLM_CONTRACT_ADDRESS,
            "YA_PAYMENT_NETWORK": "polygon",
        },
        "driver": "erc20",
        "network": "polygon",
        "token": "GLM",
    },
}


@dataclass
class PaymentConfig:
    """All payment-related config for a single container."""

    env: Dict[str, str]
    driver: str
    network: str
    platform_string: str = field(init=False)
    token: str

    def __post_init__(self):
        self.platform_string = f"{self.driver}-{self.network}-{self.token.lower()}"


def get_payment_config(payment_config_name: str) -> PaymentConfig:
    """Translate "payment-config" from goth-config.yml to a PaymentConfig instance."""
    try:
        payment_config_kwargs = _payment_config[payment_config_name]
    except KeyError:
        raise KeyError(f"Unknown payment config name: {payment_config_name}")

    return PaymentConfig(**payment_config_kwargs)
