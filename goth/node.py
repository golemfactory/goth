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


def node_environment(
    rest_api_url_base: str = "", account_list: str = ""
) -> Dict[str, str]:
    """Construct an environment for executing commands in a yagna docker container."""

    daemon_env = {
        "CENTRAL_NET_HOST": f"{ROUTER_HOST}:{ROUTER_PORT}",
        # TODO: Remove after 0.7.x is released, 0.6.x still requires it to be compatible
        "ERC20_RINKEBY_GETH_ADDR": "http://ethereum:8545",
        "RINKEBY_GETH_ADDR": "http://ethereum:8545",
        "GSB_URL": YAGNA_BUS_URL.substitute(host="0.0.0.0"),
        "IDLE_AGREEMENT_TIMEOUT": "600s",
        "MEAN_CYCLIC_BCAST_INTERVAL": "5s",
        "MEAN_CYCLIC_UNSUBSCRIBES_INTERVAL": "5s",
        "REQUIRED_CONFIRMATIONS": "1",
        "RINKEBY_TGLM_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
        "RUST_BACKTRACE": "1",
        "RUST_LOG": "debug,tokio_core=info,tokio_reactor=info,hyper=info",
        "YA_PAYMENT_NETWORK": "rinkeby",
        "YAGNA_API_URL": YAGNA_REST_URL.substitute(host="0.0.0.0"),
        "ZKSYNC_FAUCET_ADDR": "http://zksync:3030/zk/donatex",
        "ZKSYNC_RINKEBY_RPC_ADDRESS": "http://zksync:3030",
        # left for compatibility with yagna prior to commit 800efe13
        "ZKSYNC_RPC_ADDRESS": "http://zksync:3030",
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

    return node_env
