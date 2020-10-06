"""Test harness runner class, creating the nodes and running the scenario."""

import asyncio
from datetime import datetime
import functools
from itertools import chain
import logging
import os
from pathlib import Path
import subprocess
import time
from typing import cast, Dict, List, Optional, Type, TypeVar

import docker

from goth.assertions import TemporalAssertionError
from goth.runner.agent import AgentMixin
from goth.runner.container.compose import get_compose_services, COMPOSE_FILE
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.exceptions import ContainerNotFoundError, CommandError, TimeoutError
from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEventMonitor
from goth.runner.probe import Probe
from goth.runner.proxy import Proxy
from goth import helpers

logger = logging.getLogger(__name__)

ProbeType = TypeVar("ProbeType", bound=Probe)

RUN_COMMAND_SLEEP_INTERVAL = 0.1
RUN_COMMAND_DEFAULT_TIMEOUT = 3600


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

    topology: List[YagnaContainerConfig]
    """A list of configuration objects for the containers to be instantiated."""

    _static_monitors: Dict[str, LogEventMonitor]
    """Log monitors for containers running as part of docker-compose."""

    yagna_commit_hash: Optional[str]
    """Commit hash indicating the version of yagna which should be used."""

    def __init__(
        self,
        topology: List[YagnaContainerConfig],
        api_assertions_module: Optional[str],
        logs_path: Path,
        assets_path: Path,
        yagna_commit_hash: Optional[str] = None,
    ):
        self.topology = topology
        self.api_assertions_module = api_assertions_module
        self.assets_path = assets_path
        self.yagna_commit_hash = yagna_commit_hash
        self.probes = []
        self.proxy = None
        self._static_monitors = {}

        test_name = self._get_current_test_name()
        logger.info("Running test: %s", test_name)

        self.base_log_dir = logs_path / test_name

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

        for config in self.topology:
            log_config = config.log_config or LogConfig(config.name)
            log_config.base_dir = scenario_dir

            probe = config.probe_type(
                self, docker_client, config, log_config, self.assets_path
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

    def _start_nodes(self):
        node_names: Dict[str, str] = {}

        # Start the probes' containers and obtain their IP addresses
        for probe in self.probes:
            probe.start()
            assert probe.ip_address
            node_names[probe.ip_address] = probe.name

        node_names["172.19.0.1"] = "Pytest-Requestor-Agent"

        # Start the proxy node. The containers should not make API calls
        # up to this point.
        self.proxy = Proxy(
            node_names=node_names, assertions_module=self.api_assertions_module
        )
        self.proxy.start()

        for probe in self.get_probes(probe_type=AgentMixin):
            probe.start_agent()

    @staticmethod
    def _run_command(
        args,
        env: Optional[dict] = None,
        log_prefix: Optional[str] = None,
        timeout: int = RUN_COMMAND_DEFAULT_TIMEOUT,
    ):
        logger.info("Running local command: %s", " ".join(args))

        if log_prefix is None:
            log_prefix = f"[{args[0]}] "

        starttime = time.time()
        returncode = None

        p = subprocess.Popen(
            args=args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        assert p.stdout  # silence mypy
        out_queue = helpers.IOStreamQueue(p.stdout)

        while time.time() < starttime + timeout and returncode is None:
            for line in out_queue.lines():
                logger.debug("%s%s", log_prefix, line.decode("utf-8").rstrip())

            returncode = p.poll()
            if returncode is None:
                time.sleep(RUN_COMMAND_SLEEP_INTERVAL)

            if returncode:
                raise CommandError(
                    f"Command exited abnormally. args={args}, returncode={returncode}"
                )

        if returncode is None:
            p.kill()
            raise TimeoutError(
                f"Timeout exceeded while running command. "
                f"args={args}, timeout={timeout}"
            )

    def _setup_docker_compose(self):
        self._run_command(
            ["docker-compose", "-f", str(COMPOSE_FILE), "up", "-d", "--build"],
            env={"YAGNA_COMMIT_HASH": self.yagna_commit_hash}
            if self.yagna_commit_hash
            else None,
        )

    def _shutdown_docker_compose(self):
        self._run_command(["docker-compose", "-f", str(COMPOSE_FILE), "stop"])
        self._run_command(["docker-compose", "-f", str(COMPOSE_FILE), "rm", "-f"])

    async def __aenter__(self) -> "Runner":
        self._setup_docker_compose()

        self.base_log_dir.mkdir()
        self._create_probes(self.base_log_dir)
        self._start_static_monitors(self.base_log_dir)

        self._start_nodes()
        return self

    # Argument exception will be re-raised after exiting the context manager,
    # see: https://docs.python.org/3/reference/datamodel.html#object.__exit__
    async def __aexit__(self, _exc_type, _exc, _traceback):
        await asyncio.sleep(2.0)
        for probe in self.probes:
            logger.info("stopping probe. name=%s", probe.name)
            await probe.stop()

        for name, monitor in self._static_monitors.items():
            logger.debug("stopping static monitor. name=%s", name)
            await monitor.stop()

        self.proxy.stop()

        self._shutdown_docker_compose()

        # Stopping the proxy triggered evaluation of assertions
        # "at the end of events".
        self.check_assertion_errors()
