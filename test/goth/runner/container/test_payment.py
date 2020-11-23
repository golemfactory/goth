"""Test the `runner.container.payment` module."""

import pytest

from goth.runner.container.payment import (
    KeyPoolDepletedError,
    PaymentDriver,
    PaymentIdPool,
)


@pytest.fixture
def payment_id_pool() -> PaymentIdPool:
    """Pool of payment IDs for tests from this file."""
    return PaymentIdPool()


def test_get_accounts(payment_id_pool):
    """Test if pre-funded payment accounts are generated correctly."""
    drivers = [PaymentDriver.ngnt, PaymentDriver.zksync]
    receive = False
    send = False

    account_list = payment_id_pool.get_accounts(drivers, receive, send)

    # We should get back exactly 2 accounts
    assert len(account_list) == len(drivers)
    # There should be an account for each of the requested payment drivers
    result_drivers = [a.driver for a in account_list]
    for driver in drivers:
        assert driver in result_drivers
    # All accounts should have the requested receive/send values
    for account in account_list:
        assert account.receive == receive
        assert account.send == send


def test_key_pool_depleted(payment_id_pool):
    """Test if the proper exception is raised when we run out of pre-funded keys."""

    with pytest.raises(KeyPoolDepletedError):
        for i in range(100):
            payment_id_pool.get_accounts()
