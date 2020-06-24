""" Module containing constants and templates related to addresses commonly used in
    the context of yagna and the test harness. """
from string import Template
from typing import Dict, Mapping


class DefaultTemplate(Template):
    """ Extension of `Template` which allows for specifying default values for template
        fields. """

    def __init__(self, template: str, default: Dict[str, object]):
        self.default = default
        super().__init__(template)

    def substitute(self, mapping: Mapping[str, object] = {}, **kwargs):
        return super(DefaultTemplate, self).substitute(
            self._with_default(mapping), **kwargs
        )

    def safe_substitute(self, mapping: Mapping[str, object] = {}, **kwargs):
        return super(DefaultTemplate, self).safe_substitute(
            self._with_default(mapping), **kwargs
        )

    def __repr__(self):
        return f"<DefaultTemplate template={self.template}, default={self.default},>"

    def __str__(self):
        return self.substitute()

    def _with_default(self, mapping: Mapping[str, object]):
        """ Make a copy of the defaults mapping and then extend and/or overwrite the
            copy with entries from `mapping`. Allows for passing in a `mapping` dict
            alongside `kwargs` in `substitute` and `safe_substitute`. """
        default_copy = self.default.copy()
        default_copy.update(mapping)
        return default_copy


_BASE_URL_TEMPLATE = "$protocol://$host:$port"

MARKET_HOST = "mock-api"
MARKET_PORT = 5001
MARKET_PROTOCOL = "http"
MARKET_BASE_URL = DefaultTemplate(
    _BASE_URL_TEMPLATE,
    {"host": MARKET_HOST, "port": MARKET_PORT, "protocol": MARKET_PROTOCOL},
)

PROXY_HOST = "proxy"

ROUTER_HOST = "router"
ROUTER_PORT = 7477
ROUTER_PROTOCOL = "tcp"
ROUTER_BASE_URL = DefaultTemplate(
    _BASE_URL_TEMPLATE,
    {"host": ROUTER_HOST, "port": ROUTER_PORT, "protocol": ROUTER_PROTOCOL},
)

ACTIVITY_API_URL = Template("$base/activity-api/v1")
MARKET_API_URL = DefaultTemplate(
    "$base/market-api/v1", default={"base": str(MARKET_BASE_URL)}
)
PAYMENT_API_URL = Template("$base/payment-api/v1")

YAGNA_BUS_PORT = 6010
YAGNA_BUS_PROTOCOL = "tcp"
YAGNA_BUS_URL = DefaultTemplate(
    _BASE_URL_TEMPLATE, default={"port": YAGNA_BUS_PORT, "protocol": YAGNA_BUS_PROTOCOL}
)

YAGNA_REST_PORT = 6000
YAGNA_REST_PROTOCOL = "http"
YAGNA_REST_URL = DefaultTemplate(
    _BASE_URL_TEMPLATE,
    default={"port": YAGNA_REST_PORT, "protocol": YAGNA_REST_PROTOCOL},
)
