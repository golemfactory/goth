"""Test if "payment_config" in `goth-config.yml` works as expected."""
from pathlib import Path
import pytest

from goth.configuration import load_yaml

EXPECTED_PAYMENT_ENV = {
    "polygon": {
        "YA_PAYMENT_NETWORK": "polygon",
        "POLYGON_GETH_ADDR": "http://ethereum-polygon:8545",
        "POLYGON_GLM_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
        "POLYGON_MULTI_PAYMENT_CONTRACT_ADDRESS": "0xFf807885934003A35b1284d7445fc83Fd23417e5",
        "POLYGON_LOCK_PAYMENT_CONTRACT_ADDRESS": "0xD756fb6A081CC11e7F513C39399DB296b1DE3036",
        "ERC20_POLYGON_REQUIRED_CONFIRMATIONS": 0,
        "PAYMENT_CYCLE_DEFAULT_INTERVAL": "25s",
        "PAYMENT_CYCLE_DEFAULT_EXTRA_PAY_TIME": "15s",
    },
    "erc20_mainnet": {
        "YA_PAYMENT_NETWORK": "mainnet",
        "MAINNET_GETH_ADDR": "http://ethereum-mainnet:8545",
        "MAINNET_GLM_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
        "MAINNET_MULTI_PAYMENT_CONTRACT_ADDRESS": "0xFf807885934003A35b1284d7445fc83Fd23417e5",
        "MAINNET_LOCK_PAYMENT_CONTRACT_ADDRESS": "0xD756fb6A081CC11e7F513C39399DB296b1DE3036",
        "ERC20_MAINNET_REQUIRED_CONFIRMATIONS": 0,
        "PAYMENT_CYCLE_DEFAULT_INTERVAL": "25s",
        "PAYMENT_CYCLE_DEFAULT_EXTRA_PAY_TIME": "15s",
    },
    "erc20": {
        "YA_PAYMENT_NETWORK": "hoodi",
        "HOODI_GETH_ADDR": "http://ethereum-hoodi:8545",
        "HOODI_TGLM_CONTRACT_ADDRESS": "0xFDFEF9D10d929cB3905C71400ce6be1990EA0F34",
        "HOODI_MULTI_PAYMENT_CONTRACT_ADDRESS": "0xFf807885934003A35b1284d7445fc83Fd23417e5",
        "HOODI_LOCK_PAYMENT_CONTRACT_ADDRESS": "0xD756fb6A081CC11e7F513C39399DB296b1DE3036",
        "ERC20_HOODI_REQUIRED_CONFIRMATIONS": 0,
        "PAYMENT_CYCLE_DEFAULT_INTERVAL": "25s",
        "PAYMENT_CYCLE_DEFAULT_EXTRA_PAY_TIME": "15s",
    },
}


@pytest.mark.asyncio
async def test_default_payment_platform(default_goth_config: Path) -> None:
    """Test if we have "erc20" platform when none is specified."""
    goth_config = load_yaml(default_goth_config)
    for container in goth_config.containers:
        expected_payment_env = EXPECTED_PAYMENT_ENV["erc20"]
        env = container.environment
        for key, val in expected_payment_env.items():
            assert env[key] == val


@pytest.mark.parametrize("payment_config", ("erc20_mainnet", "erc20", "polygon"))
@pytest.mark.asyncio
async def test_payment_platform_env(default_goth_config: Path, payment_config) -> None:
    """Test if "payment_config" param in config file works."""
    requestor_node = {
        "name": "requestor",
        "type": "Requestor",
        "use-proxy": True,
        "payment-config": payment_config,
    }
    overrides = [("nodes", [requestor_node])]
    goth_config = load_yaml(default_goth_config, overrides)
    requestor_container = goth_config.containers[0]

    expected_payment_env = EXPECTED_PAYMENT_ENV[payment_config]
    env = requestor_container.environment

    for key, val in expected_payment_env.items():
        assert env[key] == val


@pytest.mark.asyncio
async def test_invalid_payment_config(default_goth_config: Path) -> None:
    """Test if we get KeyError for invalid payment config name."""
    requestor_node = {
        "name": "requestor",
        "type": "Requestor",
        "use-proxy": True,
        "payment-config": "OOOOPS_NO_SUCH_CONFIG",
    }
    overrides = [("nodes", [requestor_node])]
    with pytest.raises(KeyError):
        load_yaml(default_goth_config, overrides)
