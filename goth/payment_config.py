from dataclasses import dataclass
from typing import Dict

# def payments_env(payments: str) -> Dict[str, str]:
#     """Payment-related part of the environment."""
# 
#     contract_address = "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34"
#     ethereum_container_url = "http://ethereum:8545"
#     payments_env = {
#         'polygon': {
#             "YA_PAYMENT_NETWORK": "polygon",
#             "POLYGON_GETH_ADDR": ethereum_container_url,
#             "POLYGON_GLM_CONTRACT_ADDRESS": contract_address,
#         },
#         'mainnet': {
#             "YA_PAYMENT_NETWORK": "mainnet",
#             "MAINNET_GETH_ADDR": ethereum_container_url,
#             "MAINNET_GLM_CONTRACT_ADDRESS": contract_address,
#         },
#         'zksync': {
#             #   TODO: For some reason, "rinkeby" works and "mainnet" doesn't. Why?
#             "YA_PAYMENT_NETWORK": "rinkeby",
#             "ZKSYNC_FAUCET_ADDR": "http://zksync:3030/zk/donatex",
#             "ZKSYNC_RINKEBY_RPC_ADDRESS": "http://zksync:3030",
#         },
#     }
#     return payments_env[payments]



_payment_config = {
    'zksync': {
        'env': {
            "YA_PAYMENT_NETWORK": "rinkeby",
            "ZKSYNC_FAUCET_ADDR": "http://zksync:3030/zk/donatex",
            "ZKSYNC_RINKEBY_RPC_ADDRESS": "http://zksync:3030",
        },
        'driver': 'zksync',
        'network': 'rinkeby',
        'token': 'tGLM',
    },
    'erc20': {
        'env': {
            "YA_PAYMENT_NETWORK": "mainnet",
            "MAINNET_GETH_ADDR": "http://ethereum:8545",
            "MAINNET_GLM_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
        },
        'driver': 'erc20',
        'network': 'mainnet',
        'token': 'GLM',
    },
}


@dataclass
class PaymentConfig:
    env: Dict[str, str]
    driver: str
    network: str
    token: str


def get_payment_config(name: str) -> PaymentConfig:
    try:
        payment_config_kwargs = _payment_config[name]
    except KeyError:
        raise KeyError(f"Unknown payment config name: {name}")

    return PaymentConfig(**payment_config_kwargs)
