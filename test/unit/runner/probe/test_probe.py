"""Unit tests for the goth.runner.probe.Probe class."""
import pytest
from unittest.mock import MagicMock

from goth.address import YAGNA_REST_PORT, YAGNA_REST_URL
import goth.runner.container.yagna
from goth.runner.probe import Probe


@pytest.mark.parametrize("use_proxy", [False, True])
@pytest.mark.asyncio
async def test_get_yagna_api_url(monkeypatch, use_proxy: bool):
    """Test if get_yagna_api_url() returns correct URL for given use_proxy setting."""

    monkeypatch.setattr(goth.runner.probe, "YagnaContainer", MagicMock)

    probe = Probe(
        runner=MagicMock(),
        client=MagicMock(),
        config=MagicMock(use_proxy=use_proxy),
        log_config=MagicMock(),
    )
    probe.ip_address = "1.2.3.4"
    probe.container.ports = {YAGNA_REST_PORT: "6789"}

    if use_proxy:
        expected_url = YAGNA_REST_URL.substitute(host="127.0.0.1", port="6789")
    else:
        expected_url = YAGNA_REST_URL.substitute(host=probe.ip_address)

    assert probe.get_yagna_api_url() == expected_url
