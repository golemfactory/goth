"""Test harness runner class, creating the nodes and running the scenario."""

import asyncio
from contextlib import asynccontextmanager, AsyncExitStack
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

import docker

from goth.runner.agent import AgentMixin
from goth.runner.container.compose import (
    ComposeConfig,
    ComposeNetworkManager,
    run_compose_network,
)
from goth.runner.container.yagna import YagnaContainerConfig
import goth.runner.container.payment as payment
from goth.runner.exceptions import TestFailure, TemporalAssertionError
from goth.runner.log import LogConfig
from goth.runner.probe import Probe, create_probe, run_probe
from goth.runner.proxy import Proxy, run_proxy
from goth.runner.step import step  # noqa: F401
from goth.runner.web_server import WebServer, run_web_server


logger = logging.getLogger(__name__)

ProbeType = TypeVar("ProbeType", bound=Probe)


class Runner:
    """Manages the nodes and runs the scenario on them."""

    api_assertions_module: Optional[str]
    """Name of the module containing assertions to be loaded into the API monitor."""

    base_log_dir: Path
    """Base directory for all log files created during this test run."""

    probes: List[Probe]
    """Probes used for the test run."""

    proxy: Optional[Proxy]
    """An embedded instance of mitmproxy."""

    _test_failure_callback: Callable[[TestFailure], None]
    """A function to be called when `TestFailure` is caught during a test run."""

    _cancellation_callback: Callable[[], None]
    """A function to be called when `CancellationError` is caught during a test run."""

    _compose_manager: ComposeNetworkManager
    """Manager for the docker-compose network portion of the test."""

    _exit_stack: AsyncExitStack
    """A stack of `AsyncContextManager` instances to be closed on runner shutdown."""

    _topology: List[YagnaContainerConfig]
    """A list of configuration objects for the containers to be instantiated."""

    _web_server: WebServer
    """A built-in web server."""

    def __init__(
        self,
        api_assertions_module: Optional[str],
        logs_path: Path,
        compose_config: ComposeConfig,
        test_failure_callback: Callable[[TestFailure], None],
        cancellation_callback: Callable[[], None],
        web_root_path: Path,
        web_server_port: Optional[int] = None,
    ):
        self.api_assertions_module = api_assertions_module
        self.base_log_dir = logs_path / self._get_current_test_name()
        self.probes = []
        self.proxy = None
        self._exit_stack = AsyncExitStack()
        self._test_failure_callback = test_failure_callback
        self._cancellation_callback = cancellation_callback
        self._compose_manager = ComposeNetworkManager(
            config=compose_config,
            docker_client=docker.from_env(),
        )
        self._web_server = WebServer(web_root_path, web_server_port)

    def get_probes(
        self, probe_type: Type[ProbeType], name: str = ""
    ) -> List[ProbeType]:
        """Get probes by name or type.

        `probe_type` can be a type directly inheriting from `Probe`, as well as a
        mixin type used with probes. This type is used in an `isinstance` check.
        """
        probes = self.probes
        if name:
            probes = [p for p in probes if p.name == name]
        probes = [p for p in probes if isinstance(p, probe_type)]
        return cast(List[ProbeType], probes)

    def check_assertion_errors(self) -> None:
        """If any monitor reports an assertion error, raise the first error."""

        agent_probes = self.get_probes(probe_type=AgentMixin)  # type: ignore

        monitors = chain.from_iterable(
            (
                (probe.container.logs for probe in self.probes),
                (probe.agent_logs for probe in agent_probes),
                [self.proxy.monitor] if self.proxy else [],
            )
        )
        failed = chain.from_iterable(
            monitor.failed for monitor in monitors if monitor is not None
        )
        for assertion in failed:
            # We assume all failed assertions were already reported
            # in their corresponding log files. Now we only need to raise
            # one of them to break the execution.
            raise TemporalAssertionError(assertion.name)

    def _create_probes(self, scenario_dir: Path) -> None:
        docker_client = docker.from_env()

        for config in self._topology:
            logger.debug(
                "Creating probe. config=%s, probe_type=%s", config, config.probe_type
            )
            log_config = config.log_config or LogConfig(config.name)
            log_config.base_dir = scenario_dir

            probe = self._exit_stack.enter_context(
                create_probe(self, docker_client, config, log_config)
            )
            self.probes.append(probe)

    def _get_current_test_name(self) -> str:
        test_name = os.environ.get("PYTEST_CURRENT_TEST")
        assert test_name
        logger.debug("Raw current pytest test=%s", test_name)
        # Take only the function name of the currently running test
        test_name = test_name.split("::")[-1].split()[0]
        logger.debug("Cleaned current test dir name=%s", test_name)
        return test_name

    async def _start_nodes(self):
        node_names: Dict[str, str] = {}
        ports: Dict[str, dict] = {}

        # Start the probes' containers and obtain their IP addresses
        for probe in self.probes:
            ip_address = await self._exit_stack.enter_async_context(run_probe(probe))
            node_names[ip_address] = probe.name
            container_ports = probe.container.ports
            ports[ip_address] = container_ports
            logger.debug(
                "Probe for %s started on IP: %s with port mapping: %s",
                probe.name,
                ip_address,
                container_ports,
            )

        node_names[self.host_address] = "Pytest-Requestor-Agent"

        # Stopping the proxy triggers evaluation of assertions at "the end of events".
        # Install a callback to to check for assertion failures after the proxy stops.
        self._exit_stack.callback(self.check_assertion_errors)

        # Start the proxy node. The containers should not make API calls
        # up to this point.
        self.proxy = Proxy(
            node_names=node_names,
            ports=ports,
            assertions_module=self.api_assertions_module,
        )
        self._exit_stack.enter_context(run_proxy(self.proxy))

        # Collect all agent enabled probes and start them in parallel
        awaitables = []
        for probe in self.get_probes(probe_type=AgentMixin):
            awaitables.append(probe.start_agent())
        await asyncio.gather(*awaitables)

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
    def web_server_port(self) -> int:
        """Return the port of the build-in web server."""
        return self._web_server.server_port

    @property
    def web_root_path(self) -> Path:
        """Return the directory served by the built-in web server."""
        return self._web_server.root_path

    @asynccontextmanager
    async def __call__(
        self, topology: List[YagnaContainerConfig]
    ) -> AsyncGenerator["Runner", None]:
        """Set up a test with the given topology and enter the test context.

        This is an async context manager, yielding its `Runner` instance.
        """
        self._topology = topology
        _install_sigint_handler()
        try:
            try:
                await self._enter()
                yield self
            except asyncio.CancelledError:
                self._cancellation_callback()
            finally:
                await self._exit()
        except TestFailure as err:
            self._test_failure_callback(err)

    async def _enter(self) -> None:
        logger.info("Running test: %s", self._get_current_test_name())

        self.base_log_dir.mkdir()

        await self._exit_stack.enter_async_context(
            run_compose_network(self._compose_manager, self.base_log_dir)
        )

        self._create_probes(self.base_log_dir)

        await self._exit_stack.enter_async_context(
            # listen on all interfaces
            run_web_server(self._web_server, server_address=None)
        )

        await self._start_nodes()

    async def _exit(self):
        logger.info("Test finished: %s", self._get_current_test_name())
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
