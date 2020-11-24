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


def test_get_id(payment_id_pool):
    """Test if pre-funded payment accounts are generated correctly."""
    drivers = [PaymentDriver.ngnt, PaymentDriver.zksync]
    receive = False
    send = False

    payment_id = payment_id_pool.get_id(drivers, receive, send)

    # We should get back exactly 2 accounts
    assert len(payment_id.accounts) == len(drivers)
    # There should be an account for each of the requested payment drivers
    result_drivers = [a.driver for a in payment_id.accounts]
    for driver in drivers:
        assert driver in result_drivers
    # All accounts should have the requested receive/send values
    for account in payment_id.accounts:
        assert account.receive == receive
        assert account.send == send


def test_key_pool_depleted(payment_id_pool):
    """Test if the proper exception is raised when we run out of pre-funded keys."""

    with pytest.raises(KeyPoolDepletedError):
        while True:
            payment_id_pool.get_id()
