"""Tests for the `runner.cli.yagna_payment_cmd` module"""

import time

import pytest

from src.runner.cli import Cli
from .conftest import yagna_daemon_running


def test_payment_init(yagna_container):
    """Test basic usage of `payment init` command."""

    yagna = Cli(yagna_container).yagna

    with yagna_daemon_running(yagna_container):

        # The test fails if we call `payment init` too fast
        time.sleep(3.0)
        yagna.payment_init()


def test_payment_init_with_address(yagna_container):
    """Test `payment init` with explicit node address."""

    yagna = Cli(yagna_container).yagna

    with yagna_daemon_running(yagna_container):

        default_identity = yagna.id_show()
        yagna.payment_init(address=default_identity.address)

        another_identity = yagna.id_create()
        yagna.payment_init(address=another_identity.address)


@pytest.mark.skip(reason="Not sure what is the expected behaviour")
def test_payment_init_provider_mode(yagna_container):
    """Test `payment init -p`."""

    yagna = Cli(yagna_container).yagna

    with yagna_daemon_running(yagna_container):

        default_identity = yagna.id_show()
        yagna.payment_init(provider_mode=True, address=default_identity.address)


@pytest.mark.skip(reason="Not sure what is the expected behaviour")
def test_payment_init_requestor_mode(yagna_container):
    """Test `payment init -r`."""

    yagna = Cli(yagna_container).yagna

    with yagna_daemon_running(yagna_container):

        default_identity = yagna.id_show()
        yagna.payment_init(requestor_mode=True, address=default_identity.address)


def test_payment_status(yagna_container):
    """Test `payment status` subcommand."""

    yagna = Cli(yagna_container).yagna

    with yagna_daemon_running(yagna_container):

        # The test fails if we call `payment init` too fast
        time.sleep(3.0)
        status = yagna.payment_status()
        assert status


def test_payment_status_with_address(yagna_container):
    """Test `payment status` with explicit node address."""

    yagna = Cli(yagna_container).yagna

    with yagna_daemon_running(yagna_container):

        default_id = yagna.id_show()
        status = yagna.payment_status(address=default_id.address)
        assert status
