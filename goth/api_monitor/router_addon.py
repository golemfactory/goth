"""Mitmproxy addon that routes API calls.

Also, adds caller and callee information to request headers.
"""

import logging
from typing import Mapping

from mitmproxy.http import HTTPFlow
from goth.address import (
    HOST_REST_PORT_END,
    HOST_REST_PORT_START,
    YAGNA_REST_PORT,
)


CALLER_HEADER = "X-Caller"
CALLEE_HEADER = "X-Callee"


class RouterAddon:
    """Add-on for mitmproxy to set request headers and route calls.

    This add-on does the following:
    - parses the port on which the original request has been made by API client,
    - sets "X-Caller" and "X-Calle" request headers, so that they can be used
      by subsequent add-ons,
    - routes the request to the appropriate callee, based on the request port.
    """

    _logger: logging.Logger

    _node_names: Mapping[str, str]
    """Mapping of IP addresses to node names"""

    _ports: Mapping[str, dict]
    """Mapping of IP addresses to their port mappings"""

    def __init__(self, node_names: Mapping[str, str], ports: Mapping[str, dict]):
        self._logger = logging.getLogger(__name__)
        self._node_names = node_names
        self._ports = ports

    # pylint: disable = no-self-use
    def request(self, flow: HTTPFlow) -> None:
        """Route the request and set `X-Caller` and `X-Callee` headers."""

        req = flow.request
        self._logger.debug("incoming request %s, headers: %s", req, req.headers)

        try:
            server_addr = req.headers["X-Server-Addr"]
            server_port = int(req.headers["X-Server-Port"])
            remote_addr = req.headers["X-Remote-Addr"]
            node_name = self._node_names[remote_addr]

            if server_port == YAGNA_REST_PORT:
                # It's a provider agent calling a yagna daemon
                # Since we assume that the provider agent runs on the same container
                # as the provider daemon, we route this request to that container's
                # host-mapped daemon port
                req.host = "127.0.0.1"
                req.port = self._ports[remote_addr][server_port]
                req.headers[CALLER_HEADER] = f"{node_name}:agent"
                req.headers[CALLEE_HEADER] = f"{node_name}:daemon"

            elif HOST_REST_PORT_START <= server_port <= HOST_REST_PORT_END:
                # It's a requestor agent calling a yagna daemon.
                # We use localhost as the address together with the original port,
                # since each daemon has its API port mapped to a port on the host
                # chosen from the specified range.
                req.host = "127.0.0.1"
                req.port = server_port
                req.headers[CALLER_HEADER] = f"{node_name}:agent"
                req.headers[CALLEE_HEADER] = f"{node_name}:daemon"

            else:
                flow.kill()
                raise ValueError(f"Invalid server port: {server_port}")

            self._logger.debug(
                "Request from %s for %s:%d/%s routed to %s at %s:%d",
                # request caller:
                req.headers[CALLER_HEADER],
                # original host, port and path:
                server_addr,
                server_port,
                req.path,
                # request recipient:
                req.headers[CALLEE_HEADER],
                # rewritten host and port:
                req.host,
                req.port,
            )

        except (KeyError, ValueError) as ex:
            self._logger.error("Invalid request: %s, error: %s", req, ex.args[0])
            flow.kill()
            raise
