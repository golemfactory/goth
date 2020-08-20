"""Helper class for yagna node environment variables and Volumes."""

from string import Template
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

VOLUMES = {
    Template("$assets_path"): "/asset",
    Template("$assets_path/presets.json"): "/presets.json",
}


def node_environment(
    market_url_base: str = "", rest_api_url_base: str = "", account_list: str = ""
) -> Dict[str, str]:
    """Construct an environment for executing commands in a yagna docker container."""
    # Use custom base if given, default otherwise
    market_template_params = {"base": market_url_base} if market_url_base else {}

    daemon_env = {
        "CENTRAL_MARKET_URL": MARKET_API_URL.substitute(market_template_params),
        "CENTRAL_NET_HOST": f"{ROUTER_HOST}:{ROUTER_PORT}",
        "CHAIN": "mainnet",
        "GETH_ADDRESS": "http://ethereum:8545",
        "GNT2_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
        "GSB_URL": YAGNA_BUS_URL.substitute(host="0.0.0.0"),
        "YAGNA_API_URL": YAGNA_REST_URL.substitute(host="0.0.0.0"),
        "RUST_BACKTRACE": "1",
        "RUST_LOG": "debug,tokio_core=info,tokio_reactor=info,hyper=info",
        "REQUIRED_CONFIRMATIONS": "1",
    }
    if account_list:
        daemon_env["ACCOUNT_LIST"] = account_list
    node_env = daemon_env

    if rest_api_url_base:
        agent_env = {
            "YAGNA_MARKET_URL": MARKET_API_URL.substitute(base=rest_api_url_base),
            "YAGNA_ACTIVITY_URL": ACTIVITY_API_URL.substitute(base=rest_api_url_base),
            "YAGNA_PAYMENT_URL": PAYMENT_API_URL.substitute(base=rest_api_url_base),
        }
        node_env.update(agent_env)

    return node_env
