"""Tests for the `runner.cli.yagna_payment_cmd` module."""

from goth.runner.cli import Cli


def test_payment_init(yagna_container):
    """Test basic usage of `payment init` command."""

    yagna = Cli(yagna_container).yagna

    yagna.payment_init()


def test_payment_init_provider_mode(yagna_container):
    """Test `payment init --receiver`."""

    yagna = Cli(yagna_container).yagna

    yagna.payment_init(receiver_mode=True)


def test_payment_init_requestor_mode(yagna_container):
    """Test `payment init --sender`."""

    yagna = Cli(yagna_container).yagna

    yagna.payment_init(sender_mode=True)


def test_payment_status(yagna_container):
    """Test `payment status` subcommand."""

    yagna = Cli(yagna_container).yagna

    status = yagna.payment_status()
    assert status


def test_payment_status_with_address(yagna_container):
    """Test `payment status` with explicit node address."""

    yagna = Cli(yagna_container).yagna

    status = yagna.payment_status()
    assert status
