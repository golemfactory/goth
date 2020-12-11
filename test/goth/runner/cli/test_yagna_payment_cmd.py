"""Tests for the `runner.cli.yagna_payment_cmd` module."""

import time

import pytest

from goth.runner.cli import Cli


def test_payment_init(yagna_container):
    """Test basic usage of `payment init` command."""

    yagna = Cli(yagna_container).yagna

    # The test fails if we call `payment init` too fast
    time.sleep(3.0)
    yagna.payment_init()


def test_payment_status(yagna_container):
    """Test `payment status` subcommand."""

    yagna = Cli(yagna_container).yagna

    # The test fails if we call `payment init` too fast
    time.sleep(3.0)
    status = yagna.payment_status()
    assert status


def test_payment_status_with_address(yagna_container):
    """Test `payment status` with explicit node address."""

    yagna = Cli(yagna_container).yagna

    status = yagna.payment_status()
    assert status
