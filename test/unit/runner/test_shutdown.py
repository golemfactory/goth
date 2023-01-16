"""Unit tests that check if a Runner instance is shut down correctly."""

import asyncio
from pathlib import Path
from unittest import mock
import tempfile

import docker
import pytest

from goth.runner import TestFailure, Runner, PROXY_NGINX_SERVICE_NAME
from goth.runner.container.compose import ComposeNetworkManager, ContainerInfo
import goth.runner.container.utils
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.probe import Probe
from goth.runner.proxy import Proxy
from goth.runner.web_server import WebServer
from goth.payment_config import get_payment_config


TestFailure.__test__ = False


@pytest.fixture(autouse=True)
def apply_global_monkeypatches(monkeypatch):
    """Apply monkey patches for all tests."""

    monkeypatch.setattr(docker, "from_env", mock.MagicMock())
    monkeypatch.setattr(goth.runner.probe, "get_container_address", mock.MagicMock())
    monkeypatch.setattr(goth.runner.probe.Probe, "name", mock.MagicMock())
    monkeypatch.setattr(ComposeNetworkManager, "network_gateway_address", mock.MagicMock())
    monkeypatch.setattr(Probe, "ip_address", mock.MagicMock())


topology = [
    YagnaContainerConfig(
        name="requestor",
        probe_type=Probe,
        payment_config=get_payment_config("zksync"),
        volumes={},
        environment={},
        payment_id=mock.MagicMock(),
    ),
    YagnaContainerConfig(
        name="provider",
        probe_type=Probe,
        payment_config=get_payment_config("zksync"),
        volumes={},
        environment={},
        privileged_mode=False,
    ),
]


class MockError(Exception):
    """A custom exception class to distinguish mock errors from genuine ones."""


def mock_runner(test_failure_callback=None, cancellation_callback=None):
    """Return a Runner instance built from mock arguments."""

    return Runner(
        base_log_dir=Path(tempfile.mkdtemp()),
        compose_config=mock.MagicMock(),
        test_failure_callback=test_failure_callback,
        cancellation_callback=cancellation_callback,
        web_root_path=mock.MagicMock(),
    )


@pytest.fixture
def mock_function(monkeypatch):
    """Return a function that performs monkey-patching of functions or coroutines."""

    def _mock_function(class_, method, fails=0, result=None):

        call = f"{class_.__name__}.{method}()"
        mock_ = mock.MagicMock()
        mock_.name = call
        mock_.failed = False

        def _func(*args):
            if fails:
                print(f"{call} fails")
                mock_.failed = True
                raise MockError(mock_)
            print(f"{call} succeeds")
            return result

        async def _coro(*args):
            return _func(*args)

        if asyncio.iscoroutinefunction(class_.__dict__[method]):
            mock_.side_effect = _coro
        else:
            mock._side_effect = _func
        monkeypatch.setattr(class_, method, mock_)
        if method == "__init__":
            mock_.return_value = None
        return mock_

    return _mock_function


MOCK_CONTAINER_INFO = {
    "whatever": ContainerInfo("doesn't really matter", PROXY_NGINX_SERVICE_NAME, "who cares?")
}


@pytest.mark.parametrize(
    "manager_start_fails, webserver_start_fails, "
    "probe_init_fails, probe_start_fails, proxy_start_fails, "
    "check_assertion_fails, "
    "proxy_stop_fails, probe_stop_fails, probe_remove_fails, "
    "webserver_stop_fails, manager_stop_fails",
    [
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0),
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1),
        (0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0),
        (0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0),
        (0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0),
        (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1),
    ],
)
@pytest.mark.asyncio
async def test_runner_startup_shutdown(
    caplog,
    mock_function,
    manager_start_fails,
    webserver_start_fails,
    probe_init_fails,
    probe_start_fails,
    proxy_start_fails,
    check_assertion_fails,
    proxy_stop_fails,
    probe_stop_fails,
    probe_remove_fails,
    webserver_stop_fails,
    manager_stop_fails,
):
    """Test if runner components are started and shut down correctly."""

    manager_start_network = mock_function(
        ComposeNetworkManager,
        "start_network",
        manager_start_fails,
        result=MOCK_CONTAINER_INFO,
    )
    manager_stop_network = mock_function(ComposeNetworkManager, "stop_network", manager_stop_fails)
    web_server_start = mock_function(WebServer, "start", webserver_start_fails)
    web_server_stop = mock_function(WebServer, "stop", webserver_stop_fails)
    probe_init = mock_function(
        goth.runner.container.yagna.YagnaContainer, "__init__", probe_init_fails
    )
    probe_remove = mock_function(Probe, "remove", probe_remove_fails)
    probe_start = mock_function(Probe, "start", probe_start_fails)
    probe_stop = mock_function(Probe, "stop", probe_stop_fails)
    proxy_start = mock_function(Proxy, "start", proxy_start_fails)
    proxy_stop = mock_function(Proxy, "stop", proxy_stop_fails)
    runner_check_assertions = mock_function(Runner, "check_assertion_errors", check_assertion_fails)

    runner = mock_runner()

    try:
        async with runner(topology):
            pass
    except MockError as err:
        failed_mock = err.args[0]
        assert failed_mock.failed
        print("Failed:", failed_mock.name)

    assert manager_start_network.called
    assert manager_stop_network.called

    assert web_server_stop.call_count == web_server_start.call_count <= 1
    assert web_server_start.called or manager_start_network.failed
    assert proxy_stop.call_count == proxy_start.call_count <= 1
    assert runner_check_assertions.call_count == proxy_start.call_count
    assert probe_remove.call_count == probe_init.call_count <= 2
    assert probe_stop.call_count == probe_start.call_count <= 2

    # Below we assert that each component is started only after the components
    # it depends on start successfully.
    assert web_server_start.called or manager_start_network.failed
    assert probe_init.called or manager_start_network.failed or web_server_start.failed
    assert probe_start.called or (
        manager_start_network.failed or web_server_start.failed or probe_init.failed
    )
    assert proxy_start.called or (
        manager_start_network.failed
        or web_server_start.failed
        or probe_init.failed
        or probe_start.failed
    )
    if proxy_start.failed:
        assert "Starting probes failed: MockError" in caplog.text


_FUNCTIONS_TO_MOCK = (
    (
        ComposeNetworkManager,
        ("start_network", "stop_network"),
        (MOCK_CONTAINER_INFO, None),
    ),
    (WebServer, ("start", "stop"), (None, None)),
    (Probe, ("remove", "start", "stop"), (None, None, None)),
    (Proxy, ("start", "stop"), (None, None)),
    (Runner, ("check_assertion_errors",), (None,)),
)


@pytest.mark.parametrize("have_test_failure", [False, True])
@pytest.mark.asyncio
async def test_runner_test_failure(mock_function, have_test_failure):
    """Test if test failure callback is called if a TestFailure is raised."""

    for class_, funcs, results in _FUNCTIONS_TO_MOCK:
        for func, result in zip(funcs, results):
            mock_function(class_, func, result=result)

    test_failure_callback = mock.MagicMock()
    runner = mock_runner(test_failure_callback=test_failure_callback)

    async with runner(topology):
        if have_test_failure:
            raise TestFailure("some test failed!")

    assert test_failure_callback.called == have_test_failure


@pytest.mark.parametrize("cancel", [True, False])
@pytest.mark.asyncio
async def test_runner_cancelled(mock_function, cancel):
    """Test that cancellation callback is called if a runner is cancelled."""

    for class_, funcs, results in _FUNCTIONS_TO_MOCK:
        for func, result in zip(funcs, results):
            mock_function(class_, func, result=result)

    cancellation_callback = mock.MagicMock()
    runner = mock_runner(cancellation_callback=cancellation_callback)

    async with runner(topology):
        if cancel:
            raise asyncio.CancelledError()

    assert cancellation_callback.called == cancel
