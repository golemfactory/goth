"""Mitmproxy addon that routes API calls and adds caller and callee
information to request headers
"""

import logging

from mitmproxy.http import HTTPFlow


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s", level=logging.DEBUG,
)

# `mitmproxy` adds ugly prefix to add-on module names
logger = logging.getLogger(__name__.replace("__mitmproxy_script__.", ""))


PORT_MAPPING = {
    15001: (5001, "RequestorDaemon", "Market"),
    15002: (5001, "RequestorAgent", "Market"),
    16000: (6000, "RequestorAgent", "RequestorDaemon"),
    15003: (5001, "ProviderDaemon", "Market"),
    15004: (5001, "ProviderAgent", "Market"),
    16001: (6001, "ProviderAgent", "ProviderDaemon"),
}

CALLER_HEADER = "X-Caller"
CALLEE_HEADER = "X-Callee"


class RouterAddon:
    """
    This add-on does the following:
    - parses the port on which the original request has been made by API client,
    - sets "X-Caller" and "X-Calle" request headers, so that they can be used
      by subsequent add-ons,
    - routes the request to the appropriate callee, based on the request port.
    """

    # pylint: disable = no-self-use
    def request(self, flow: HTTPFlow):
        """Route the request and set `X-Caller` and `X-Callee` headers"""
        req = flow.request
        try:
            http_host = req.headers["X-Http-Host"]
            # original_port may be used to distinguish clients accessing
            # the same API and to route the message to the appropriate
            # upstream API server
            original_port = int(http_host[http_host.rindex(":") + 1 :])
            if original_port in PORT_MAPPING:
                dest_port, caller, callee = PORT_MAPPING[original_port]
                req.port = dest_port
                req.headers[CALLER_HEADER] = caller
                req.headers[CALLEE_HEADER] = callee
                logger.debug(
                    "Route message: %d (%s) -> %d (%s)",
                    original_port,
                    caller,
                    req.port,
                    callee,
                )
            else:
                raise ValueError(f"Invalid port in 'X-Http-Host': {http_host}")
        except (KeyError, ValueError) as ex:
            logger.error("Invalid headers: %s", ex.args[0])


# This is used by mitmproxy to install add-ons
addons = [RouterAddon()]
