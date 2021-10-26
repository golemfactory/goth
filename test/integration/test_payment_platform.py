from pathlib import Path
import pytest

from goth.configuration import load_yaml

EXPECTED_PAYMENT_ENV = {
    'polygon': {
        "MUMBAI_TGLM_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
        "MUMBAI_GETH_ADDR": "http://ethereum:8545",
        "YA_PAYMENT_NETWORK": "mumbai",
    },
    'zksync': {
        #   TODO: leave only variables we need

        # TODO: Remove after 0.7.x is released, 0.6.x still requires it to be compatible
        "ERC20_RINKEBY_GETH_ADDR": "http://ethereum:8545",

        "RINKEBY_GETH_ADDR": "http://ethereum:8545",
        "RINKEBY_TGLM_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
        "YA_PAYMENT_NETWORK": "rinkeby",
        "ZKSYNC_FAUCET_ADDR": "http://zksync:3030/zk/donatex",
        "ZKSYNC_RINKEBY_RPC_ADDRESS": "http://zksync:3030",

        # left for compatibility with yagna prior to commit 800efe13
        "ZKSYNC_RPC_ADDRESS": "http://zksync:3030",
    }
}


@pytest.mark.asyncio
async def test_payment_platform(default_goth_config: Path, log_dir: Path) -> None:
    overrides = [
        (
            "nodes",
            [
                {"name": "requestor", "type": "Requestor", "use-proxy": True},
                {"name": "provider-1", "type": "VM-Wasm-Provider", "use-proxy": True,
                    "payments": "zksync"},
                {"name": "provider-2", "type": "VM-Wasm-Provider", "use-proxy": True,
                    "payments": "polygon"},
            ],
        )
    ]
    goth_config = load_yaml(default_goth_config, overrides)
    for container in goth_config.containers:
        if container.name == 'provider-2':
            payments = 'polygon'
        else:
            payments = "zksync"

        expected_payment_env = EXPECTED_PAYMENT_ENV[payments]
        env = container.environment

        for key, val in expected_payment_env.items():
            assert env[key] == val
