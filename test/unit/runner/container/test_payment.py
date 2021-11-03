"""Test the `runner.container.payment` module."""

import pytest

from goth.runner.container.payment import (
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


def test_key_pool_depleted(payment_id_pool):
    """Test if the proper exception is raised when we run out of pre-funded keys."""

    any_payment_config = get_payment_config("zksync")
    with pytest.raises(KeyPoolDepletedError):
        while True:
            payment_id_pool.get_id(any_payment_config)
