"""Transport address helper.

Module containing constants and templates related to addresses commonly used in
the context of yagna and the test harness.

Note: the variables defining ports are also used in the `nginx.conf` file
in the proxy container. If you rename any of them here then make sure to also
apply the same renaming in `nginx.conf`.
"""
from string import Template
from typing import Dict, Mapping, Optional


def ensure_no_trailing_slash(input: str) -> str:
    """Remove the trailing slash from `input`."""
    if input[-1] == "/":
        input = input[:-1]
    return input


class DefaultTemplate(Template):
    """Extend `Template` to allow for default values for template fields."""

    def __init__(self, template: str, default: Dict[str, object]):
        """Set the default and initialise Template()."""

        self.default = default
        super().__init__(template)

    def substitute(self, mapping: Optional[Mapping[str, object]] = None, **kwargs):
        """Replace values in string with `mapping`, merge default and mapping first."""
        return super(DefaultTemplate, self).substitute(
            self._with_default(mapping or {}), **kwargs
        )

    def safe_substitute(self, mapping: Optional[Mapping[str, object]] = None, **kwargs):
        """Replace values in string with `mapping`, merge default and mapping first.

        Safe means that instead of raising a `KeyError` if a value for a placeholder is
        missing, the placeholder will appear in the result string.
        """
        return super(DefaultTemplate, self).safe_substitute(
            self._with_default(mapping or {}), **kwargs
        )

    def __repr__(self):
        return f"<DefaultTemplate template={self.template}, default={self.default},>"

    def __str__(self):
        return self.substitute()

    def _with_default(self, mapping: Mapping[str, object]):
        """Merge `self.default` with `mapping`.

        Make a copy of the defaults mapping and then extend and/or overwrite the copy
        with entries from `mapping`. Allows for passing in a `mapping` dict alongside
        `kwargs` in `substitute` and `safe_substitute`.
        """
        default_copy = self.default.copy()
        default_copy.update(mapping)
        return default_copy


_BASE_URL_TEMPLATE = "$protocol://$host:$port"

PROXY_HOST = "proxy-nginx"

ROUTER_HOST = "router"
ROUTER_PORT = 7477
ROUTER_PROTOCOL = "tcp"
ROUTER_BASE_URL = DefaultTemplate(
    _BASE_URL_TEMPLATE,
    {"host": ROUTER_HOST, "port": ROUTER_PORT, "protocol": ROUTER_PROTOCOL},
)

ACTIVITY_API_URL = Template("$base/activity-api/v1/")
MARKET_API_URL = Template("$base/market-api/v1/")
PAYMENT_API_URL = Template("$base/payment-api/v1/")

YAGNA_BUS_PORT = 6010
YAGNA_BUS_PROTOCOL = "tcp"
YAGNA_BUS_URL = DefaultTemplate(
    _BASE_URL_TEMPLATE, default={"port": YAGNA_BUS_PORT, "protocol": YAGNA_BUS_PROTOCOL}
)

# NOTE: This variable is used in `nginx.conf` file in the proxy container
# also, because it needs to be host-mapped in order for the tests to be runnable
# on non-Linux platforms, it's also independently specified in the definition for the
# `proxy-nginx` service in `docker-compose.yml`
YAGNA_REST_PORT = 6000

YAGNA_REST_PROTOCOL = "http"
YAGNA_REST_URL = DefaultTemplate(
    _BASE_URL_TEMPLATE,
    default={"port": YAGNA_REST_PORT, "protocol": YAGNA_REST_PROTOCOL},
)

# Range of ports on the host to which yagna daemon ports in containers can be mapped.
# Port $YAGNA_REST_PORT on N-th started yagna container is mapped to port
# $HOST_REST_PORT_START + (N-1) on the host.

# NOTE: This variable is used in `nginx.conf` file in the proxy container:
HOST_REST_PORT_START = 6001
# NOTE: This variable is used in `nginx.conf` file in the proxy container:
HOST_REST_PORT_END = 6100

# Ports in the range $HOST_REST_PORT_START .. $HOST_REST_PORT_END are also used
# by the nginx-proxy container. A request made to port $HOST_REST_PORT_START + (N-1)
# on nginx-proxy container is forwarded to the MITM proxy (that runs on host)
# which then forwards the request to $YAGNA_REST_PORT on the N-th yagna container.

# To enable access to those nginx-proxy ports from outside of the Docker network
# on non-Linux systems, we map ports $HOST_REST_PORT_START .. $HOST_REST_PORT_END on
# the nginx-proxy to ports ($HOST_REST_PORT_START + O) .. ($HOST_REST_PORT_END + O)
# on the host, where the offset O is the value of the variable HOST_NGINX_PORT_OFFSET
# defined below.
# NOTE: this value has to be consistent with a port mapping definition for the
# `nginx-proxy` container in `docker-compose.yml`.
HOST_NGINX_PORT_OFFSET = 10000


# Port used by the mitmproxy instance
# NOTE: This variable is used in `nginx.conf` file in the proxy container:
MITM_PROXY_PORT = 9000

# Port range used by the internal web server spawned by goth for each test
# Ports are rotated and re-used in a circular fashion
WEB_SERVER_PORT_START = 9201
WEB_SERVER_PORT_END = 9251
