"""Test harness runner class, creating the nodes and running the scenario."""

from datetime import datetime, timezone
from itertools import chain
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import docker

from goth.assertions import TemporalAssertionError
from goth.runner.container.compose import get_compose_services
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.exceptions import ContainerNotFoundError
from goth.runner.log import configure_logging, LogConfig
from goth.runner.log_monitor import LogEventMonitor
from goth.runner.probe import Probe, ProviderProbe, RequestorProbe, Role
from goth.runner.proxy import Proxy


class Runner:
    """Manages the nodes and runs the scenario on them."""

    api_assertions_module: Optional[str]
    """Name of the module containing assertions to be loaded into the API monitor."""

    assets_path: Optional[Path]
    """Path to directory containing yagna assets to be mounted in containers."""

    base_log_dir: Path
    """Base directory for all log files created during this test run."""

    probes: List[Probe]
    """Probes used for the test run."""

    proxy: Optional[Proxy]
    """An embedded instance of mitmproxy."""

    topology: List[YagnaContainerConfig]
    """A list of configuration objects for the containers to be instantiated."""

    _static_monitors: Dict[str, LogEventMonitor]
    """Log monitors for containers running as part of docker-compose."""

    def __init__(
        self,
        topology: List[YagnaContainerConfig],
        api_assertions_module: Optional[str],
        logs_path: Path,
        assets_path: Optional[Path],
    ):
        self.topology = topology
        self.api_assertions_module = api_assertions_module
        self.assets_path = assets_path
        self.probes = []
        self.proxy = None
        self._static_monitors = {}

        # Create a unique subdirectory for this test run
        date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
        self.base_log_dir = logs_path / f"yagna_integration_{date_str}"
        self.base_log_dir.mkdir(parents=True)

        configure_logging(self.base_log_dir)
        self.logger = logging.getLogger(__name__)

        scenario_dir = self.base_log_dir / self._get_test_log_dir_name()
        scenario_dir.mkdir(exist_ok=True)
        self._create_probes(scenario_dir)
        self._start_static_monitors(scenario_dir)

    def get_probes(self, role: Optional[Role] = None, name: str = "") -> List[Probe]:
        """Get probes by name or role."""
        probes = self.probes
        if role:
            probes = [p for p in probes if isinstance(p, role)]
        if name:
            probes = [p for p in probes if p.name == name]
        return probes

    def check_assertion_errors(self) -> None:
        """If any monitor reports an assertion error, raise the first error."""

        monitors = chain.from_iterable(
            (
                (probe.container.logs for probe in self.probes),
                (probe.agent_logs for probe in self.probes),
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

        for config in self.topology:
            log_config = config.log_config or LogConfig(config.name)
            log_config.base_dir = scenario_dir

            if isinstance(config, YagnaContainerConfig):
                probe = config.role(
                    self, docker_client, config, log_config, self.assets_path
                )
                self.probes.append(probe)

    def _get_test_log_dir_name(self):
        test_name = os.environ.get("PYTEST_CURRENT_TEST")
        self.logger.debug("Raw current pytest test=%s", test_name)
        # Take only the function name of the currently running test
        test_name = test_name.split("::")[-1].split()[0]
        self.logger.debug("Cleaned current test dir name=%s", test_name)
        return test_name

    def _start_static_monitors(self, scenario_dir: Path) -> None:
        docker_client = docker.from_env()

        for service_name in get_compose_services():
            log_config = LogConfig(service_name)
            log_config.base_dir = scenario_dir
            monitor = LogEventMonitor(log_config)

            container = docker_client.containers.list(filters={"name": service_name})
            if not container:
                raise ContainerNotFoundError(service_name)
            container = container[0]

            monitor.start(
                container.logs(
                    follow=True,
                    since=datetime.utcnow(),
                    stream=True,
                    timestamps=True,
                )
            )
            self._static_monitors[service_name] = monitor

    async def _stop_static_monitors(self) -> None:
        for name, monitor in self._static_monitors.items():
            self.logger.debug("stopping static monitor. name=%s", name)
            await monitor.stop()

    def _start_nodes(self):
        node_names: Dict[str, str] = {}

        # Start the probes' containers and obtain their IP addresses
        for probe in self.probes:
            probe.start_container()
            assert probe.ip_address
            node_names[probe.ip_address] = probe.name

        node_names["172.19.0.1"] = "Pytest-Requestor-Agent"

        # Start the proxy node. The containers should not make API calls
        # up to this point.
        self.proxy = Proxy(
            node_names=node_names, assertions_module=self.api_assertions_module
        )
        self.proxy.start()

        # The proxy is ready to route the API calls. Start the agents.
        for probe in self.probes:
            probe.start_agent()
