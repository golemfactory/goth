"""A class for starting an embedded instance of mitmproxy"""
import asyncio
import logging
import threading
from typing import Optional

from mitmproxy import options
import mitmproxy.utils.debug
from mitmproxy.tools import _main, cmdline, dump

from goth.assertions.monitor import EventMonitor
from goth.api_monitor.api_events import APIEvent
from goth.api_monitor.router_addon import RouterAddon
from goth.api_monitor.monitor_addon import MonitorAddon


mitmproxy.utils.debug.register_info_dumpers = lambda *args: None


class Proxy:

    monitor: EventMonitor[APIEvent]
    _proxy_thread: threading.Thread
    _logger: logging.Logger
    _loop: Optional[asyncio.AbstractEventLoop]

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        assertions_module: Optional[str] = None,
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._loop = None
        self._proxy_thread = threading.Thread(
            target=self._run_mitmproxy, name="ProxyThread", daemon=True
        )

        def _stop_callback():
            """Stop `loop` so `proxy_thread` can terminate."""
            if self._loop and self._loop.is_running():
                self._loop.stop()

        self.monitor = EventMonitor(self._logger, on_stop=_stop_callback)
        if assertions_module:
            self.monitor.load_assertions(assertions_module)

    def start(self):
        self._proxy_thread.start()

    def stop(self):

        if not self._loop:
            raise RuntimeError("Event loop is not set")
        asyncio.run_coroutine_threadsafe(self.monitor.stop(), self._loop)
        self._proxy_thread.join()

    def _run_mitmproxy(self):
        """This method is run by `self.proxy_thread`"""

        self._loop = asyncio.new_event_loop()
        # Monkey patch the loop to set its `add_signal_handler` method to no-op.
        # The original method would raise error since the loop will run in a non-main
        # thread and hence cannot have signal handlers installed.
        self._loop.add_signal_handler = lambda *args_: None
        asyncio.set_event_loop(self._loop)

        self.monitor.start()

        self._logger.info("Starting embedded mitmproxy...")

        # This class is nested since it needs to refer to the attribute `_monitor`
        # of the enclosing instance of `Proxy`.
        class MITMProxyRunner(dump.DumpMaster):
            def __init__(inner_self, opts: options.Options) -> None:
                super().__init__(opts)
                inner_self.addons.add(RouterAddon())
                inner_self.addons.add(MonitorAddon(self.monitor))

        args = "-q --mode reverse:http://127.0.0.1 --listen-port 9000".split()
        _main.run(MITMProxyRunner, cmdline.mitmdump, args)
        self._logger.info("Embedded mitmproxy exited")
