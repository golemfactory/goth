"""Mitmproxy addon that routes API calls.

Also, adds caller and callee information to request headers.
"""

import logging

from mitmproxy.http import HTTPFlow
from goth.address import MARKET_PORT, YAGNA_REST_PORT


logger = logging.getLogger(__name__)


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

    # pylint: disable = no-self-use
    def request(self, flow: HTTPFlow) -> None:
        """Route the request and set `X-Caller` and `X-Callee` headers."""

        req = flow.request

        try:
            server_addr = req.headers["X-Server-Addr"]
            server_port = int(req.headers["X-Server-Port"])
            remote_addr = req.headers["X-Remote-Addr"]
            node_num = remote_addr.rsplit(".", 1)[-1]

            if server_port == MARKET_PORT:
                # It's a yagna daemon calling the central market API.
                # We use localhost's address, since `MARKET_PORT` in the
                # market API container is mapped to the same port on the host.
                req.host = "127.0.0.1"
                req.port = MARKET_PORT
                req.headers[CALLER_HEADER] = f"Daemon-{node_num}"
                req.headers[CALLEE_HEADER] = "MarketAPI"

            elif server_port == YAGNA_REST_PORT:
                # It's an agent calling a yagna daemon
                req.host = remote_addr
                req.port = YAGNA_REST_PORT
                req.headers[CALLER_HEADER] = f"Agent-{node_num}"
                req.headers[CALLEE_HEADER] = f"Daemon-{node_num}"

            else:
                flow.kill()
                raise ValueError(f"Invalid server port: {server_port}")

            logger.debug(
                "(%s) %s:%d -> %s:%d (%s): %s",
                req.headers[CALLER_HEADER],
                server_addr,
                server_port,
                req.host,
                req.port,
                req.headers[CALLEE_HEADER],
                req.path,
            )

        except (KeyError, ValueError) as ex:
            logger.error("Invalid request: %s", ex.args[0])
            logger.error("Headers: %s", req.headers)


# This is used by mitmproxy to install add-ons
addons = [RouterAddon()]
