"""Tests for the `runner.cli.yagna_id_cmd` module"""

import pytest

from goth.runner.cli import Cli
from goth.runner.exceptions import CommandError


def test_id_create(yagna_container):
    """Test `yagna id create` without arguments."""

    yagna = Cli(yagna_container).yagna

    identity = yagna.id_create()
    assert identity.is_default is False
    assert identity.alias is None

    another_identity = yagna.id_create()
    assert identity != another_identity


def test_id_create_with_alias(yagna_container):
    """Test `yagna id create` with alias."""

    yagna = Cli(yagna_container).yagna

    identity = yagna.id_create(alias="id-alias")
    assert identity.is_default is False
    assert identity.alias == "id-alias"

    another_identity = yagna.id_create(alias="another-id-alias")
    assert another_identity.is_default is False
    assert another_identity.alias == "another-id-alias"


def test_id_create_same_alias_fails(yagna_container):
    """Test that `yagna id create` fails if the same alias was used previously."""

    yagna = Cli(yagna_container).yagna

    yagna.id_create(alias="id-alias")

    with pytest.raises(CommandError):
        yagna.id_create(alias="id-alias")


def test_id_show(yagna_container):
    """Test that `yagna show` prints default identity."""

    yagna = Cli(yagna_container).yagna

    identity = yagna.id_show()
    assert identity.is_default is True


def test_id_show_by_address(yagna_container):
    """Test `yagna show` with identity address specified."""

    yagna = Cli(yagna_container).yagna

    new_identity = yagna.id_create()
    some_identity = yagna.id_show(alias_or_addr=new_identity.address)
    assert some_identity == new_identity


def test_id_show_by_alias(yagna_container):
    """Test `yagna show` with identity alias specified."""

    yagna = Cli(yagna_container).yagna

    new_identity = yagna.id_create(alias="id-alias")
    some_identity = yagna.id_show(alias_or_addr="id-alias")
    assert some_identity == new_identity


def test_id_show_by_unknown_alias_fails(yagna_container):
    """Test that `yagna show` with nonexistent identity alias fails."""

    yagna = Cli(yagna_container).yagna

    identity = yagna.id_show(alias_or_addr="unknown-alias")
    assert identity is None


def test_id_list_default(yagna_container):
    """Test thst the result of `yagna id list` contains the default identity."""

    yagna = Cli(yagna_container).yagna

    ids = yagna.id_list()
    assert len(ids) == 1

    default_identity = yagna.id_show()
    assert ids[0] == default_identity


def test_id_list_many(yagna_container):
    """Test that the result of `yagna id list` contains all identities."""
    yagna = Cli(yagna_container).yagna

    default_identity = yagna.id_show()
    another_identity = yagna.id_create()
    yet_another_identity = yagna.id_create(alias="id-alias")

    ids = yagna.id_list()
    assert set(ids) == {
        default_identity,
        another_identity,
        yet_another_identity,
    }
