"""A class for starting an embedded instance of mitmproxy."""
import asyncio
import contextlib
import logging
import threading
from typing import AsyncIterator, Mapping, Optional

from func_timeout.StoppableThread import StoppableThread
from mitmproxy import options
import mitmproxy.utils.debug
from mitmproxy.tools import _main, cmdline, dump

from goth.address import MITM_PROXY_PORT
from goth.assertions.monitor import EventMonitor
from goth.api_monitor.api_events import APIEvent
from goth.api_monitor.router_addon import RouterAddon
from goth.api_monitor.monitor_addon import MonitorAddon
from goth.runner.exceptions import StopThreadException


# This function in `mitmproxy` will try to register signal handlers
# which will fail since the proxy does not run in the main thread.
# So we monkey-patch it to no-op.
mitmproxy.utils.debug.register_info_dumpers = lambda *args: None


logger = logging.getLogger(__name__)


class Proxy:
    """Proxy using mitmproxy to generate events out of http calls."""

    monitor: EventMonitor[APIEvent]
    _proxy_thread: StoppableThread
    _logger: logging.Logger
    _node_names: Mapping[str, str]
    _server_ready: threading.Event
    """Mapping of IP addresses to node names"""

    _ports: Mapping[str, dict]
    """Mapping of IP addresses to their port mappings"""

    def __init__(
        self,
        node_names: Mapping[str, str],
        ports: Mapping[str, dict],
        assertions_module: Optional[str] = None,
    ):
        self._node_names = node_names
        self._ports = ports
        self._logger = logging.getLogger(__name__)
        self._proxy_thread = StoppableThread(
            target=self._run_mitmproxy, name="ProxyThread", daemon=True
        )
        self._server_ready = threading.Event()

        self.monitor = EventMonitor("rest", self._logger)
        if assertions_module:
            self.monitor.load_assertions(assertions_module)

    def start(self):
        """Start the proxy thread."""
        self.monitor.start()
        self._proxy_thread.start()
        self._server_ready.wait()

    async def stop(self):
        """Stop the proxy thread and the monitor."""
        self._proxy_thread.stop(StopThreadException)
        self._proxy_thread.join()
        await self.monitor.stop()

    def _run_mitmproxy(self):
        """Ran by `self.proxy_thread`."""

        loop = asyncio.new_event_loop()
        # Monkey patch the loop to set its `add_signal_handler` method to no-op.
        # The original method would raise error since the loop will run in a non-main
        # thread and hence cannot have signal handlers installed.
        loop.add_signal_handler = lambda *args_: None
        asyncio.set_event_loop(loop)

        self._logger.info("Starting embedded mitmproxy...")

        # This class is nested since it needs to refer to the `monitor` attribute
        # of the enclosing instance of `Proxy`.
        class MITMProxyRunner(dump.DumpMaster):
            def __init__(inner_self, opts: options.Options) -> None:
                super().__init__(opts)
                inner_self.addons.add(RouterAddon(self._node_names, self._ports))
                inner_self.addons.add(MonitorAddon(self.monitor))

            def start(inner_self):
                self._server_ready.set()
                self._logger.info("Embedded mitmproxy started")
                super().start()

        args = f"-q --mode reverse:http://127.0.0.1 --listen-port {MITM_PROXY_PORT}"
        _main.run(MITMProxyRunner, cmdline.mitmdump, args.split())
        self._logger.info("Embedded mitmproxy exited")


@contextlib.asynccontextmanager
async def run_proxy(proxy: Proxy) -> AsyncIterator[Proxy]:
    """Implement AsyncContextManager protocol for starting and stopping a Proxy."""

    try:
        logger.debug("Starting mitmproxy")
        proxy.start()
        yield
    finally:
        logger.debug("Stopping mitmproxy")
        await proxy.stop()
