"""Test harness runner class, creating the nodes and running the scenario."""

import asyncio
from contextlib import asynccontextmanager, AsyncExitStack
from datetime import datetime, timezone
from itertools import chain
import logging
import os
from pathlib import Path
import sys
from typing import (
    cast,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
)

import colors
import docker

from goth.api_monitor.api_events import APIEvent
from goth.assertions.monitor import Assertion, AssertionFunction, EventMonitor
from goth.runner.container.compose import (
    ComposeConfig,
    ContainerInfo,
    ComposeNetworkManager,
    run_compose_network,
)
from goth.runner.container.yagna import YagnaContainerConfig
import goth.runner.container.payment as payment
from goth.runner.exceptions import TestFailure, TemporalAssertionError
from goth.runner.log import configure_logging_for_test, LogConfig
from goth.runner.probe import Probe, create_probe, run_probe
from goth.runner.proxy import Proxy, run_proxy
from goth.runner.step import step  # noqa: F401
from goth.runner.web_server import WebServer, run_web_server


logger = logging.getLogger(__name__)

ProbeType = TypeVar("ProbeType", bound=Probe)


PROXY_NGINX_SERVICE_NAME = "proxy-nginx"
"""Name of the nginx proxy service in the Docker network.

Must match the service name in the config file used by the runner's
compose network manager.
"""


class Runner:
    """Manages the nodes and runs the scenario on them."""

    api_assertions_module: Optional[str]
    """Name of the module containing assertions to be loaded into the API monitor."""

    log_dir: Path
    """Directory for all log files created during this test run."""

    test_name: str
    """Name of the test scenario this runner is used in."""

    probes: List[Probe]
    """Probes used for the test run."""

    proxy: Optional[Proxy]
    """An embedded instance of mitmproxy."""

    _container_info: Dict[str, ContainerInfo]
    """Info about connected containers"""

    _test_failure_callback: Callable[[TestFailure], None]
    """A function to be called when `TestFailure` is caught during a test run."""

    _cancellation_callback: Optional[Callable[[], None]]
    """A function to be called when `CancellationError` is caught during a test run.

    If not set, the error is propagated.
    """

    _compose_manager: ComposeNetworkManager
    """Manager for the docker-compose network portion of the test."""

    _exit_stack: AsyncExitStack
    """A stack of `AsyncContextManager` instances to be closed on runner shutdown."""

    _nginx_service_address: Optional[str]
    """The IP address of the nginx service in the Docker network."""

    _pending_api_assertions: List[Assertion[APIEvent]]

    _topology: List[YagnaContainerConfig]
    """A list of configuration objects for the containers to be instantiated."""

    _web_server: Optional[WebServer]
    """A built-in web server."""

    def __init__(
        self,
        base_log_dir: Path,
        compose_config: ComposeConfig,
        test_name: Optional[str] = None,
        api_assertions_module: Optional[str] = None,
        test_failure_callback: Optional[Callable[[TestFailure], None]] = None,
        cancellation_callback: Optional[Callable[[], None]] = None,
        web_root_path: Optional[Path] = None,
        web_server_port: Optional[int] = None,
    ):
        # Set up the logging directory for this runner
        self.test_name = test_name or self._current_pytest_test_name() or ""
        date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
        self.log_dir = base_log_dir / self.test_name / date_str
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.api_assertions_module = api_assertions_module
        self.probes = []
        self.proxy = None
        self._container_info = {}
        self._exit_stack = AsyncExitStack()
        self._cancellation_callback = cancellation_callback
        self._test_failure_callback = test_failure_callback
        self._compose_manager = ComposeNetworkManager(
            config=compose_config,
            docker_client=docker.from_env(),
        )
        self._nginx_service_address = None
        self._pending_api_assertions = []
        self._web_server = WebServer(web_root_path, web_server_port) if web_root_path else None

    def get_probes(self, probe_type: Type[ProbeType], name: str = "") -> List[ProbeType]:
        """Get probes by name or type.

        `probe_type` can be a type directly inheriting from `Probe`, as well as a
        mixin type used with probes. This type is used in an `isinstance` check.
        """
        probes = self.probes
        if name:
            probes = [p for p in probes if p.name == name]
        probes = [p for p in probes if isinstance(p, probe_type)]
        return cast(List[ProbeType], probes)

    def add_api_assertion(self, func: AssertionFunction, name=None) -> Assertion[APIEvent]:
        """Add an assertion for API events to this runner proxy.

        If the proxy is already running, the returned assertion will be started.
        Otherwise, the returned assertion will be started automatically when
        the proxy is started by this runner.
        """

        if self.proxy:
            return self.proxy.monitor.add_assertion(func, name)
        assertion = Assertion(func, name)
        self._pending_api_assertions.append(assertion)
        return assertion

    def check_assertion_errors(self, *extra_monitors: EventMonitor) -> None:
        """If any monitor reports an assertion error, raise the first error."""

        probe_agents = chain(*(probe.agents for probe in self.probes))

        monitors = chain.from_iterable(
            (
                (probe.container.logs for probe in self.probes),
                (agent.log_monitor for agent in probe_agents),
                [self.proxy.monitor] if self.proxy else [],
                extra_monitors,
            )
        )
        failed = chain.from_iterable(monitor.failed for monitor in monitors if monitor is not None)
        for assertion in failed:
            # We assume all failed assertions were already reported
            # in their corresponding log files. Now we only need to raise
            # one of them to break the execution.
            raise TemporalAssertionError(assertion.name)

    def get_container_info(self) -> Dict[str, ContainerInfo]:
        return self._container_info

    def _create_probes(self, scenario_dir: Path) -> None:
        docker_client = docker.from_env()

        for config in self._topology:
            log_config = config.log_config or LogConfig(config.name)
            log_config.base_dir = scenario_dir

            probe = self._exit_stack.enter_context(
                create_probe(self, docker_client, config, log_config)
            )
            self.probes.append(probe)

    def _current_pytest_test_name(self) -> Optional[str]:
        test_name = os.environ.get("PYTEST_CURRENT_TEST")
        if not test_name:
            return None
        logger.debug("Raw current pytest test=%s", test_name)
        # Take only the function name of the currently running test
        test_name = test_name.split("::")[-1].split()[0]
        logger.debug("Cleaned current test dir name=%s", test_name)
        return test_name

    async def _start_nodes(self):
        node_names: Dict[str, str] = {}
        ports: Dict[str, dict] = {}

        # Start all probes as asyncio tasks in parallel, cancel them on error
        probe_tasks = [
            asyncio.create_task(self._exit_stack.enter_async_context(run_probe(probe)))
            for probe in self.probes
        ]
        try:
            future_gather = asyncio.gather(*probe_tasks)
            await future_gather
        except Exception as e:
            for task in probe_tasks:
                task.cancel()
            logger.error(f"Starting probes failed: {e!r}")
            raise e

        # Obtain the probes' IP addresses and port mappings
        for probe in self.probes:
            node_names[probe.ip_address] = probe.name
            container_ports = probe.container.ports
            ports[probe.ip_address] = container_ports
            logger.debug(
                "Probe for %s started. IP address: %s, port mapping: %s",
                probe.name,
                probe.ip_address,
                container_ports,
            )

        node_names[self.host_address] = "docker-host"

        # Stopping the proxy triggers evaluation of assertions at "the end of events".
        # Install a callback to to check for assertion failures after the proxy stops.
        self._exit_stack.callback(self.check_assertion_errors)

        # Start the proxy node. The containers should not make API calls
        # up to this point.
        await self._start_proxy(node_names, ports)

        # Collect all agent enabled probes and start them in parallel
        awaitables = [probe.start_agents() for probe in self.probes]
        await asyncio.gather(*awaitables)

    async def _start_proxy(self, node_names: Dict[str, str], ports: Dict[str, dict]) -> None:
        self.proxy = Proxy(
            node_names=node_names,
            ports=ports,
            assertions_module=self.api_assertions_module,
        )

        await self._exit_stack.enter_async_context(run_proxy(self.proxy))

        for assertion in self._pending_api_assertions:
            self.proxy.monitor.add_assertion(assertion)
        self._pending_api_assertions = []

    @property
    def host_address(self) -> str:
        """Return the host IP address in the docker network used by the containers.

        Both the proxy server and the built-in web server are bound to this address.

        On Mac (and Windows?) there's no network bridge and the services on the host
        don't have access to Docker's internal network. Thus, we need to use a special
        address `host.docker.internal`
        """

        if sys.platform == "linux":
            return self._compose_manager.network_gateway_address
        else:
            return "host.docker.internal"

    @property
    def nginx_container_address(self) -> str:
        """Return the IP address of the proxy-nginx service in the Docker network."""
        if not self._nginx_service_address:
            raise RuntimeError("Docker network not started")
        return self._nginx_service_address

    @property
    def web_server_port(self) -> Optional[int]:
        """Return the port of the build-in web server."""
        return self._web_server.server_port if self._web_server else None

    @property
    def web_root_path(self) -> Optional[Path]:
        """Return the directory served by the built-in web server."""
        return self._web_server.root_path if self._web_server else None

    @asynccontextmanager
    async def __call__(
        self, topology: List[YagnaContainerConfig]
    ) -> AsyncGenerator["Runner", None]:
        """Set up a test with the given topology and enter the test context.

        This is an async context manager, yielding its `Runner` instance.
        """
        self._topology = topology
        # check if Windows
        if "win32" not in sys.platform:
            _install_sigint_handler()
        try:
            try:
                await self._enter()
                yield self
            except asyncio.CancelledError:
                if self._cancellation_callback:
                    self._cancellation_callback()
                else:
                    raise
            finally:
                await self._exit()
        except TestFailure as err:
            if self._test_failure_callback:
                self._test_failure_callback(err)
            else:
                raise

    async def _enter(self) -> None:
        self._exit_stack.enter_context(configure_logging_for_test(self.log_dir))
        logger.info(colors.yellow("Running test: %s"), self.test_name)

        self._container_info = await self._exit_stack.enter_async_context(
            run_compose_network(self._compose_manager, self.log_dir)
        )
        for info in self._container_info.values():
            if PROXY_NGINX_SERVICE_NAME in info.aliases:
                self._nginx_service_address = info.address
                break
        else:
            raise RuntimeError(
                f"Service {PROXY_NGINX_SERVICE_NAME} not found in the Docker network"
            )

        self._create_probes(self.log_dir)

        if self._web_server:
            await self._exit_stack.enter_async_context(
                # listen on all interfaces
                run_web_server(self._web_server, server_address=None)
            )

        await self._start_nodes()

    async def _exit(self):
        logger.info(colors.yellow("Test finished: %s"), self.test_name)
        await self._exit_stack.aclose()
        payment.clean_up()


def _install_sigint_handler():
    """Install handler that cancels the current task in the current event loop."""
    import signal

    task = asyncio.current_task()
    loop = asyncio.get_event_loop()

    def _sigint_handler(*args):
        logger.warning("Received SIGINT")
        task.cancel()

    loop.add_signal_handler(signal.SIGINT, _sigint_handler)
