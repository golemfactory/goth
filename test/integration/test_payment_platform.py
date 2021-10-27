from pathlib import Path
import pytest

from goth.configuration import load_yaml

EXPECTED_PAYMENT_ENV = {
    'polygon': {
        "YA_PAYMENT_NETWORK": "polygon",
        "POLYGON_GETH_ADDR": "http://ethereum:8545",
        "POLYGON_GLM_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
    },
    'zksync': {
        "YA_PAYMENT_NETWORK": "mainnet",
        "ZKSYNC_MAINNET_RPC_ADDRESS": "http://zksync:3030",
        "ZKSYNC_FAUCET_ADDR": "http://zksync:3030/zk/donatex",
    },
    'mainnet': {
        "YA_PAYMENT_NETWORK": "mainnet",
        "MAINNET_GETH_ADDR": "http://ethereum:8545",
        "MAINNET_GLM_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
    },
}


@pytest.mark.asyncio
async def test_default_payment_platform(default_goth_config: Path) -> None:
    goth_config = load_yaml(default_goth_config)
    for container in goth_config.containers:
        expected_payment_env = EXPECTED_PAYMENT_ENV["zksync"]
        env = container.environment
        for key, val in expected_payment_env.items():
            assert env[key] == val


@pytest.mark.asyncio
async def test_payment_platform(default_goth_config: Path) -> None:
    overrides = [
        (
            "nodes",
            [
                {"name": "requestor", "type": "Requestor", "use-proxy": True,
                    "payments": "mainnet"},
                {"name": "provider-1", "type": "VM-Wasm-Provider", "use-proxy": True,
                    "payments": "zksync"},
                {"name": "provider-2", "type": "VM-Wasm-Provider", "use-proxy": True,
                    "payments": "polygon"},
            ],
        )
    ]
    goth_config = load_yaml(default_goth_config, overrides)
    for ix, container in enumerate(goth_config.containers):
        payments = ["mainnet", "zksync", "polygon"][ix]

        expected_payment_env = EXPECTED_PAYMENT_ENV[payments]
        env = container.environment

        for key, val in expected_payment_env.items():
            assert env[key] == val
