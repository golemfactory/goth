"""Mitmproxy addon that routes API calls.

Also, adds caller and callee information to request headers.
"""

import logging
from typing import Dict, Mapping

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

    _name_to_port: Dict[str, int]
    """Map a node name to the corresponding port on host.

    For example, if YAGNA_REST_PORT in the node `provider-1` is mapped
    to port `6001` on the host, then `_name_to_port["provider-1"] == 6001`.
    """

    _port_to_name: Dict[int, str]
    """The map that is inverse to `name_to_port`.

    `name_to_port` should be injective so the inverse map should be well defined.
    """

    def __init__(
        self, node_names: Mapping[str, str], ports: Mapping[str, Mapping[int, int]]
    ):
        self._logger = logging.getLogger(__name__)
        self._node_names = node_names
        self._name_to_port = {}
        self._port_to_name = {}
        for node, port_mapping in ports.items():
            if YAGNA_REST_PORT in port_mapping:
                host_port = port_mapping[YAGNA_REST_PORT]
                name = node_names[node]
                self._name_to_port[name] = host_port
                assert host_port not in self._port_to_name
                self._port_to_name[host_port] = name

    # pylint: disable = no-self-use
    def request(self, flow: HTTPFlow) -> None:
        """Route the request and set `X-Caller` and `X-Callee` headers."""

        req = flow.request
        self._logger.debug("incoming request %s, headers: %s", req, req.headers)

        try:
            server_addr = req.headers["X-Server-Addr"]
            server_port = int(req.headers["X-Server-Port"])
            remote_addr = req.headers["X-Remote-Addr"]
            agent_node = self._node_names[remote_addr]

            if server_port == YAGNA_REST_PORT:
                # This should be a request from an agent running in a yagna container
                # calling that container's daemon. We route this request to that
                # container's host-mapped daemon port.
                req.host = "127.0.0.1"
                req.port = self._name_to_port[agent_node]
                req.headers[CALLER_HEADER] = f"{agent_node}:agent"
                req.headers[CALLEE_HEADER] = f"{agent_node}:daemon"

            elif HOST_REST_PORT_START <= server_port <= HOST_REST_PORT_END:
                # This should be a request from an agent running on the Docker host
                # calling a yagna daemon in a container. We use localhost as the address
                # together with the original port, since each daemon has its API port
                # mapped to a port on the host chosen from the specified range.
                req.host = "127.0.0.1"
                req.port = server_port
                req.headers[CALLER_HEADER] = f"{agent_node}:agent"
                daemon_node = self._port_to_name[server_port]
                req.headers[CALLEE_HEADER] = f"{daemon_node}:daemon"

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
