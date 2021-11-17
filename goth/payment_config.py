"""All possible payment-related configuration, in one place."""
from dataclasses import dataclass, field
from typing import Dict

GETH_ADDR = "http://ethereum:8545"
GLM_CONTRACT_ADDRESS = "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34"
# Sets how many blocks need to be mined on the blockchain in order for a transaction
# to be considered confirmed. This is currently disabled due to ganache server not
# mining blocks automatically. See: https://github.com/golemfactory/gnt2/issues/172
REQUIRED_CONFIRMATIONS_COUNT = 0

_payment_config = {
    "zksync": {
        "env": {
            "YA_PAYMENT_NETWORK": "rinkeby",
            "ZKSYNC_FAUCET_ADDR": "http://zksync:3030/zk/donatex",
            "ZKSYNC_RINKEBY_RPC_ADDRESS": "http://zksync:3030",
        },
        "driver": "zksync",
        "network": "rinkeby",
        "token": "tGLM",
    },
    "erc20_mainnet": {
        "env": {
            "ERC20_MAINNET_REQUIRED_CONFIRMATIONS": REQUIRED_CONFIRMATIONS_COUNT,
            "MAINNET_GETH_ADDR": GETH_ADDR,
            "MAINNET_GLM_CONTRACT_ADDRESS": GLM_CONTRACT_ADDRESS,
            "YA_PAYMENT_NETWORK": "mainnet",
        },
        "driver": "erc20",
        "network": "mainnet",
        "token": "GLM",
    },
    "erc20": {
        "env": {
            "ERC20_RINKEBY_REQUIRED_CONFIRMATIONS": REQUIRED_CONFIRMATIONS_COUNT,
            "RINKEBY_GETH_ADDR": GETH_ADDR,
            "RINKEBY_TGLM_CONTRACT_ADDRESS": GLM_CONTRACT_ADDRESS,
            "YA_PAYMENT_NETWORK": "rinkeby",
        },
        "driver": "erc20",
        "network": "rinkeby",
        "token": "tGLM",
    },
    "polygon": {
        "env": {
            "ERC20_POLYGON_REQUIRED_CONFIRMATIONS": REQUIRED_CONFIRMATIONS_COUNT,
            "POLYGON_GETH_ADDR": GETH_ADDR,
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
