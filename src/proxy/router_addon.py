"""
Mitmproxy addon that routes API calls and adds caller and callee
information to request headers
"""
import logging

from mitmproxy.http import HTTPFlow


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    level=logging.DEBUG,
)

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

    logger: logging.Logger

    def __init__(self):
        self.logger = logging.getLogger("Router")

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
                self.logger.debug(
                    f"Route message: {original_port} ({caller}) "
                    f"-> {req.port} ({callee})"
                )
            else:
                raise ValueError(f"Invalid port in 'X-Http-Host': {http_host}")
        except Exception as ex:
            print(f"Invalid headers: {ex.args[0]}")


addons = [RouterAddon()]
