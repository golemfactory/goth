"""Test the `runner.container.payment` module."""

import pytest

from goth.runner.container.payment import (
    KeyNotFoundError,
    KeyPoolDepletedError,
    PaymentIdPool,
)
from goth.payment_config import get_payment_config


@pytest.fixture
def payment_id_pool() -> PaymentIdPool:
    """Pool of payment IDs for tests from this file."""
    return PaymentIdPool()


@pytest.mark.parametrize("payment_config_name", ("erc20", "zksync"))
def test_get_id(payment_id_pool, payment_config_name):
    """Test if pre-funded payment accounts are generated correctly."""
    receive = False
    send = False

    payment_config = get_payment_config(payment_config_name)
    payment_id = payment_id_pool.get_id(payment_config, receive, send)

    assert len(payment_id.accounts) == 1

    account = payment_id.accounts[0]

    assert account.driver == payment_config.driver
    assert account.token == payment_config.token
    assert account.network == payment_config.network
    assert account.receive == receive
    assert account.send == send


@pytest.mark.parametrize("payment_config_name", ("erc20", "zksync"))
def test_get_id_with_address(payment_id_pool, payment_config_name):
    """Test if pre-funded payment accounts can be found by address."""
    receive = False
    send = False

    payment_config = get_payment_config(payment_config_name)
    address_in_pool = "63fc2ad3d021a4d7e64323529a55a9442c444da0"
    payment_id = payment_id_pool.get_id(
        payment_config,
        receive,
        send,
        address=address_in_pool,
    )

    assert len(payment_id.accounts) == 1

    account = payment_id.accounts[0]

    assert account.driver == payment_config.driver
    assert account.token == payment_config.token
    assert account.network == payment_config.network
    assert account.receive == receive
    assert account.send == send


@pytest.mark.parametrize("payment_config_name", ("erc20", "zksync"))
def test_get_id_with_address_removes_from_pool(payment_id_pool, payment_config_name):
    """Test if found pre-funded payment accounts is removed from pool."""

    payment_config = get_payment_config(payment_config_name)
    address_in_pool = "63fc2ad3d021a4d7e64323529a55a9442c444da0"
    payment_id = payment_id_pool.get_id(
        payment_config,
        address=address_in_pool,
    )

    assert len(payment_id.accounts) == 1

    with pytest.raises(KeyNotFoundError):
        payment_id_pool.get_id(
            payment_config,
            address=address_in_pool,
        )


def test_key_pool_depleted(payment_id_pool):
    """Test if the proper exception is raised when we run out of pre-funded keys."""

    any_payment_config = get_payment_config("zksync")
    with pytest.raises(KeyPoolDepletedError):
        while True:
            payment_id_pool.get_id(any_payment_config)


def test_key_not_found(payment_id_pool):
    """Test if the proper exception is raised when there is no pre-funded key with specific address."""

    any_payment_config = get_payment_config("zksync")
    address_not_in_pool = "0000000000000000000000000000000000000000"
    with pytest.raises(KeyNotFoundError):
        payment_id_pool.get_id(
            any_payment_config,
            address=address_not_in_pool,
        )
