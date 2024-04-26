"""A class for starting an embedded instance of mitmproxy."""
import contextlib
import logging
from typing import AsyncIterator, Mapping, Optional

from pylproxy import PylProxy

from goth.address import MITM_PROXY_PORT
from goth.assertions.monitor import EventMonitor
from goth.api_monitor.api_events import APIEvent, APIRequest, APIResponse

logger = logging.getLogger(__name__)


class Proxy:
    """Proxy using pylproxy to generate events out of http calls."""

    monitor: EventMonitor[APIEvent]
    _logger: logging.Logger
    _node_names: Mapping[str, str]
    """Mapping of IP addresses to node names"""

    _ports: Mapping[str, dict]
    """Mapping of IP addresses to their port mappings"""

    def __init__(
        self,
        node_names: Mapping[str, str],
        ports: Mapping[str, dict],
        assertions_module: Optional[str] = None,
    ):
        self._pyl_proxy = None
        self._node_names = node_names
        self._ports = ports
        self._logger = logging.getLogger(__name__)

        self.monitor = EventMonitor("rest", self._logger)
        if assertions_module:
            self.monitor.load_assertions(assertions_module)

    async def start(self):
        """Start the proxy thread."""
        self.monitor.start()
        self._pyl_proxy = PylProxy(self._node_names, self._ports)
        await self._pyl_proxy.start(
            "0.0.0.0",
            MITM_PROXY_PORT,
            lambda request_no, request: self.monitor.add_event_sync(
                APIRequest(request_no, request)
            ),
            lambda request_no, request, response: self.monitor.add_event_sync(
                APIResponse(request_no, APIRequest(request_no, request), response)
            ),
        )

    async def stop(self):
        if self._pyl_proxy:
            await self._pyl_proxy.stop()
            self._logger.info("The pyl proxy stopped")
            await self.monitor.stop()


@contextlib.asynccontextmanager
async def run_proxy(proxy: Proxy) -> AsyncIterator[Proxy]:
    """Implement AsyncContextManager protocol for starting and stopping a Proxy."""

    try:
        logger.debug("Starting pylproxy")
        await proxy.start()
        yield
    finally:
        logger.debug("Stopping pylproxy")
        await proxy.stop()
