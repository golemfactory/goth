"""All possible payment-related configuration, in one place."""
from dataclasses import dataclass
from typing import Dict

GETH_ADDR = "http://ethereum:8545"
GLM_CONTRACT_ADDRESS = "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34"

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
    "erc20": {
        "env": {
            "YA_PAYMENT_NETWORK": "mainnet",
            "MAINNET_GETH_ADDR": GETH_ADDR,
            "MAINNET_GLM_CONTRACT_ADDRESS": GLM_CONTRACT_ADDRESS,
        },
        "driver": "erc20",
        "network": "mainnet",
        "token": "GLM",
    },
    "polygon": {
        "env": {
            "YA_PAYMENT_NETWORK": "polygon",
            "POLYGON_GETH_ADDR": GETH_ADDR,
            "POLYGON_GLM_CONTRACT_ADDRESS": GLM_CONTRACT_ADDRESS,
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
    token: str


def get_payment_config(payment_config_name: str) -> PaymentConfig:
    """Translate "payment_config" from goth-config.yml to a PaymentConfig instance."""
    try:
        payment_config_kwargs = _payment_config[payment_config_name]
    except KeyError:
        raise KeyError(f"Unknown payment config name: {payment_config_name}")

    return PaymentConfig(**payment_config_kwargs)
