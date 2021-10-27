"""Helper class for yagna node environment variables and Volumes."""

from typing import Dict

from goth.address import (
    ACTIVITY_API_URL,
    MARKET_API_URL,
    PAYMENT_API_URL,
    ROUTER_HOST,
    ROUTER_PORT,
    YAGNA_BUS_URL,
    YAGNA_REST_URL,
)

DEFAULT_SUBNET = "goth"


def payments_env(payments: str) -> Dict[str, str]:
    """Payment-related part of the environment."""

    contract_address = "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34"
    ethereum_container_url = "http://ethereum:8545"
    payments_env = {
        'polygon': {
            "YA_PAYMENT_NETWORK": "polygon",
            "POLYGON_GETH_ADDR": ethereum_container_url,
            "POLYGON_GLM_CONTRACT_ADDRESS": contract_address,
        },
        'mainnet': {
            "YA_PAYMENT_NETWORK": "mainnet",
            "MAINNET_GETH_ADDR": ethereum_container_url,
            "MAINNET_GLM_CONTRACT_ADDRESS": contract_address,
        },
        'zksync': {
            #   TODO: For some reason, "rinkeby" works and "mainnet" doesn't. Why?
            "YA_PAYMENT_NETWORK": "rinkeby",
            "ZKSYNC_FAUCET_ADDR": "http://zksync:3030/zk/donatex",
            "ZKSYNC_RINKEBY_RPC_ADDRESS": "http://zksync:3030",
        },
    }
    return payments_env[payments]


def node_environment(
    payments: str, rest_api_url_base: str = "", account_list: str = ""
) -> Dict[str, str]:
    """Construct an environment for executing commands in a yagna docker container."""

    daemon_env = {
        "CENTRAL_NET_HOST": f"{ROUTER_HOST}:{ROUTER_PORT}",
        # TODO: Remove after 0.7.x is released, 0.6.x still requires it to be compatible
        "GSB_URL": YAGNA_BUS_URL.substitute(host="0.0.0.0"),
        "IDLE_AGREEMENT_TIMEOUT": "600s",
        "MEAN_CYCLIC_BCAST_INTERVAL": "5s",
        "MEAN_CYCLIC_UNSUBSCRIBES_INTERVAL": "5s",
        "REQUIRED_CONFIRMATIONS": "1",
        "RUST_BACKTRACE": "1",
        "RUST_LOG": "debug,tokio_core=info,tokio_reactor=info,hyper=info",
        "YAGNA_API_URL": YAGNA_REST_URL.substitute(host="0.0.0.0"),
    }
    if account_list:
        daemon_env["ACCOUNT_LIST"] = account_list
    node_env = daemon_env

    if rest_api_url_base:
        agent_env = {
            # Setting URLs for all three APIs has the same effect as setting
            # YAGNA_API_URL to YAGNA_REST_URL.substitute(base=rest_api_url_base).
            # We set all three separately so it's easier to selectively disable
            # proxy for certain APIs (if a need to do so arises).
            "YAGNA_ACTIVITY_URL": ACTIVITY_API_URL.substitute(base=rest_api_url_base),
            "YAGNA_MARKET_URL": MARKET_API_URL.substitute(base=rest_api_url_base),
            "YAGNA_PAYMENT_URL": PAYMENT_API_URL.substitute(base=rest_api_url_base),
        }
        node_env.update(agent_env)

    node_env.update(payments_env(payments))

    return node_env
