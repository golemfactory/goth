"""Test harness runner class, creating the nodes and running the scenario."""

import asyncio
from contextlib import asynccontextmanager
import functools
from itertools import chain
import logging
import os
from pathlib import Path
import time
from typing import cast, AsyncGenerator, Dict, List, Optional, Type, TypeVar

import docker

from goth.assertions import TemporalAssertionError
from goth.runner.agent import AgentMixin
from goth.runner.container.compose import ComposeConfig, ComposeNetworkManager
from goth.runner.container.yagna import YagnaContainerConfig
import goth.runner.container.payment as payment
from goth.runner.log import LogConfig
from goth.runner.probe import Probe
from goth.runner.proxy import Proxy
from goth.runner.web_server import WebServer


logger = logging.getLogger(__name__)

ProbeType = TypeVar("ProbeType", bound=Probe)


def step(default_timeout: float = 10.0):
    """Wrap a step function to implement timeout and log progress."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: Probe, *args, timeout: Optional[float] = None):
            timeout = timeout if timeout is not None else default_timeout
            step_name = f"{self.name}.{func.__name__}(timeout={timeout})"
            start_time = time.time()

            logger.info("Running step '%s'", step_name)
            try:
                result = await asyncio.wait_for(func(self, *args), timeout=timeout)
                self.runner.check_assertion_errors()
                step_time = time.time() - start_time
                logger.debug(
                    "Finished step '%s', result: %s, time: %s",
                    step_name,
                    result,
                    step_time,
                )
            except Exception as exc:
                step_time = time.time() - start_time
                logger.error(
                    "Step '%s' raised %s in %s",
                    step_name,
                    exc.__class__.__name__,
                    step_time,
                )
                raise
            return result

        return wrapper

    return decorator


DEFAULT_WEB_SERVER_PORT = 8080


class Runner:
    """Manages the nodes and runs the scenario on them."""

    api_assertions_module: Optional[str]
    """Name of the module containing assertions to be loaded into the API monitor."""

    assets_path: Path
    """Path to directory containing yagna assets to be mounted in containers."""

    base_log_dir: Path
    """Base directory for all log files created during this test run."""

    probes: List[Probe]
    """Probes used for the test run."""

    proxy: Optional[Proxy]
    """An embedded instance of mitmproxy."""

    _compose_manager: ComposeNetworkManager
    """Manager for the docker-compose network portion of the test."""

    _topology: List[YagnaContainerConfig]
    """A list of configuration objects for the containers to be instantiated."""

    _web_server: WebServer
    """A built-in web server."""

    def __init__(
        self,
        api_assertions_module: Optional[str],
        logs_path: Path,
        assets_path: Path,
        compose_config: ComposeConfig,
        web_server_port: int = DEFAULT_WEB_SERVER_PORT,
    ):
        self.api_assertions_module = api_assertions_module
        self.assets_path = assets_path
        self.base_log_dir = logs_path / self._get_current_test_name()
        self.probes = []
        self.proxy = None
        self._compose_manager = ComposeNetworkManager(
            config=compose_config,
            docker_client=docker.from_env(),
        )
        self._web_server = WebServer(self.web_root_path, web_server_port)

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
            raise TemporalAssertionError(
                f"Assertion '{assertion.name}' failed, cause: {assertion.result}"
            )

    def _create_probes(self, scenario_dir: Path) -> None:
        docker_client = docker.from_env()

        for config in self._topology:
            log_config = config.log_config or LogConfig(config.name)
            log_config.base_dir = scenario_dir

            probe = config.probe_type(self, docker_client, config, log_config)
            for name, value in config.probe_properties.items():
                probe.__setattr__(name, value)
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

        # Start the probes' containers and obtain their IP addresses
        for probe in self.probes:
            await probe.start()
            assert probe.ip_address
            node_names[probe.ip_address] = probe.name

        node_names[self.host_address] = "Pytest-Requestor-Agent"

        # Start the proxy node. The containers should not make API calls
        # up to this point.
        self.proxy = Proxy(
            node_names=node_names, assertions_module=self.api_assertions_module
        )
        self.proxy.start()
        # Wait for proxy to start. TODO: wait for a log line?
        await asyncio.sleep(2.0)

        # Collect all agent enabled probes and start them in parallel
        awaitables = []
        for probe in self.get_probes(probe_type=AgentMixin):
            awaitables.append(probe.start_agent())
        await asyncio.gather(*awaitables)

    @property
    def host_address(self) -> str:
        """Return the host IP address in the docker network used by the containers.

        Both the proxy server and the built-in web server are bound to this address.
        """
        return self._compose_manager.network_gateway_address

    @property
    def web_server_port(self) -> int:
        """Return the port of the build-in web server."""
        return self._web_server.server_port

    @property
    def web_root_path(self) -> Path:
        """Return the directory served by the built-in web server."""

        return self.assets_path / "web-root"

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
            await self._enter()
            yield self
        except asyncio.CancelledError:
            logger.error("The runner was cancelled")
            raise
        finally:
            await self._exit()

    async def _enter(self) -> None:
        logger.info("Running test: %s", self._get_current_test_name())

        self.base_log_dir.mkdir()
        await self._compose_manager.start_network(self.base_log_dir)

        self._create_probes(self.base_log_dir)
        await self._web_server.start(self.host_address)
        await self._start_nodes()

    async def _exit(self):
        logger.info("Test finished: %s", self._get_current_test_name())

        for probe in self.probes:
            await probe.stop()

        self.proxy.stop()
        # Stopping the proxy triggered evaluation of assertions
        # "at the end of events".
        self.check_assertion_errors()

        await self._compose_manager.stop_network()
        await self._web_server.stop()

        # Clean up temporary files left by the test
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
