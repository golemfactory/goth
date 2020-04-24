"""
Mitmproxy addon that traces API calls and verifies
that the sequence of calls satifies given properties
"""
from __future__ import annotations
import importlib
import logging
import queue
import threading
from typing import Callable, List, Optional, Sequence, Tuple

import mitmproxy
from mitmproxy.flow import Error
from mitmproxy.http import HTTPFlow, HTTPRequest, HTTPResponse

from router_addon import CALLER_HEADER, CALLEE_HEADER


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    level=logging.DEBUG,
)


class APICall:
    """
    Represents an API call, consisting of a HTTP Request and an optional
    HTTP Response and Error.

    Calls are ordered by request time.
    """

    request: HTTPRequest
    response: Optional[HTTPResponse]
    error: Optional[Error]

    def __init__(self, request: HTTPRequest):
        self.request = request
        self.response = None
        self.error = None

    @property
    def in_progress(self) -> bool:
        """Does this call await for a response?"""
        return self.response is None and self.error is None

    @property
    def failed(self) -> bool:
        """Did this call end with an error?"""
        return self.error is not None

    @property
    def caller(self) -> Optional[str]:
        """Return the caller name"""
        return self.request.headers.get(CALLER_HEADER)

    @property
    def callee(self) -> Optional[str]:
        """Return the callee name"""
        return self.request.headers.get(CALLEE_HEADER)

    def __str__(self):
        return (
            f"{self.caller} -> {self.callee}.{self.request.method}"
            f"({self.request.path})"
        )


class Property:
    """Represents a property of a sequence of API calls"""

    # Name for printing
    label: str

    # Function that check whether this property holds for a given sequence
    check: Callable[[Sequence[APICall], logging.Logger], bool]

    def __init__(self, func):
        self.label = func.__name__
        self.check = func


def trace_property(func: Property):
    """To be used as decorator that wraps functions as properties"""
    return Property(func)


class CallTrace:
    """
    Represents a sequence of API calls and a set of properties
    that the sequence has to satisfy.

    Since adding a new request to the sequence may trigger checking
    if all properties are satified, every instance of this class
    starts a separate thread that performs all the checks without
    blocking the client.
    """

    # List of API calls registered so far
    calls: List[APICall]

    # Calls to register are taken from this queue
    incoming: queue.Queue[HTTPFlow]

    # All heavy work is done in a separate thread
    worker: threading.Thread

    # List of properties that have to be checked for each new call
    # Each property is stored with a label that is used in log messages
    properties: List[Tuple[str, Property]]

    logger: logging.Logger
    call_logger: logging.Logger

    def __init__(self):
        self.calls = []
        self.incoming = queue.Queue()
        self.properties = []
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.logger = logging.getLogger("CallTracer")

        # Setup call logging to "calls.log" file
        self.call_logger = logging.getLogger("Calls")
        log_handler = logging.FileHandler("calls.log", mode="w")
        log_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(num)-4s %(status)-5s %(caller)-15s -> "
                "%(callee)-16s %(method)-6s %(path)s"
            )
        )
        self.call_logger.handlers = [log_handler]

    def load_properties(self, module_name: str) -> None:
        """Load property functions from a module"""
        self.logger.info(f"Loading properties from {module_name}")
        mod = importlib.import_module(module_name)
        for _, elem in mod.__dict__.items():
            # This test is lame, but simply checking if `type(elem)`
            # is equal to `Property` does not work here (why?):
            elem_type = type(elem)
            same_module = (
                Property.__module__ == elem_type.__module__
                or Property.__module__.endswith("." + elem_type.__module__)
            )
            if same_module and elem_type.__name__ == Property.__name__:
                self.properties.append(elem)
        self.logger.info(f"{len(self.properties)} properties loaded")

    def start(self) -> None:
        """Start tracing API calls"""
        self.worker.start()
        self.logger.info("Tracing started")

    def add(self, flow: HTTPFlow) -> None:
        """Register a new HTTP request/response/error"""
        self.incoming.put(flow)

    def __del__(self) -> None:
        # This will eventually terminate the worker thread:
        self.incoming.put(None)

    def __len__(self) -> int:
        """Return the number of registered calls"""
        return len(self.calls)

    def _run(self) -> None:
        """
        Run the thread that adds incomming requests/responses/errors
        to the trace and checks the properties
        """
        while True:
            flow = self.incoming.get()
            if flow is None:
                # it's time to finish
                break

            num, call = self._find_or_create_call(flow)

            if flow.error or flow.response:
                call.error = flow.error
                call.response = flow.response

            status = (
                "sent" if call.in_progress else "error" if call.failed else "ok"
            )
            self.logger.info(f"{call}:\t{status}")
            self.call_logger.info(
                f"{call}:\t{status}",
                extra={
                    "num": num,
                    "caller": call.caller,
                    "callee": call.callee,
                    "method": call.request.method,
                    "path": call.request.path,
                    "status": status,
                },
            )

            self._check_properties()

    def _find_or_create_call(self, flow: HTTPFlow) -> Tuple[int, APICall]:
        """Find a call by request or create a new one"""

        if flow.response or flow.error:
            # A matching request may have already been registered
            for num, call in enumerate(reversed(self.calls)):
                if call.request == flow.request:
                    return len(self.calls) - num, call

        call = APICall(flow.request)
        self.calls.append(call)
        return len(self.calls), call

    def _check_properties(self) -> None:
        for prop in self.properties:
            if not prop.check(self.calls, self.logger):
                index = len(self.calls)
                self.logger.warning(f"Property {prop.label} failed at {index}")


class TracerAddon:
    """This add-on keeps track of API calls"""

    trace: CallTrace

    def __init__(self):
        self.trace = CallTrace()

    def load(self, loader):
        """Load module with property functions"""
        loader.add_option(
            name="properties",
            typespec=Optional[str],
            default=None,
            help="A file with the properties to check",
        )
        mitmproxy.ctx.options.process_deferred()
        props_path = mitmproxy.ctx.options.properties
        if props_path is not None:
            self.trace.load_properties(props_path)
        self.trace.start()

    def request(self, flow: HTTPFlow) -> None:
        """Register a request"""
        self.trace.add(flow)

    def response(self, flow: HTTPFlow):
        """Register a response"""
        self.trace.add(flow)

    def error(self, flow: HTTPFlow):
        """Register an error"""
        self.trace.add(flow)


addons = [TracerAddon()]
