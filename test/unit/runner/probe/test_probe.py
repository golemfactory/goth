"""Unit tests for the goth.runner.probe.Probe class."""
import pytest
from unittest.mock import MagicMock

from goth.address import YAGNA_REST_PORT, YAGNA_REST_URL, HOST_NGINX_PORT_OFFSET
import goth.runner.container.yagna
from goth.runner.probe import Probe


@pytest.mark.parametrize("use_proxy", [False, True])
@pytest.mark.asyncio
async def test_get_yagna_api_url(monkeypatch, use_proxy: bool):
    """Test if get_yagna_api_url() returns correct URL for given use_proxy setting."""

    monkeypatch.setattr(goth.runner.probe, "YagnaContainer", MagicMock())

    host_mapped_port = 6789
    host_mapped_nginx_port = HOST_NGINX_PORT_OFFSET + host_mapped_port

    probe = Probe(
        runner=MagicMock(),
        client=MagicMock(),
        config=MagicMock(use_proxy=use_proxy, payment_id=None),
        log_config=MagicMock(),
    )
    probe.container.ports = {YAGNA_REST_PORT: host_mapped_port}

    if use_proxy:
        expected_url = YAGNA_REST_URL.substitute(host="127.0.0.1", port=host_mapped_nginx_port)
    else:
        expected_url = YAGNA_REST_URL.substitute(host="127.0.0.1", port=host_mapped_port)

    assert probe.get_yagna_api_url() == expected_url
