"""Classes and helpers for managing Probes."""

import abc
import asyncio
import logging
from pathlib import Path
import re
import time
from typing import Optional, Type, TYPE_CHECKING

from docker import DockerClient

from goth.assertions.operators import eventually
from goth.runner.cli import Cli, YagnaDockerCli
from goth.runner.container.utils import get_container_address
from goth.runner.container.yagna import YagnaContainer, YagnaContainerConfig
from goth.runner.exceptions import KeyAlreadyExistsError
from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEvent, LogEventMonitor

if TYPE_CHECKING:
    from goth.runner import Runner

logger = logging.getLogger(__name__)


class ProbeLoggingAdapter(logging.LoggerAdapter):
    """Adds probe name information to log messages."""

    EXTRA_PROBE_NAME = "probe_name"

    def process(self, msg, kwargs):
        """Process the log message."""
        return "[%s] %s" % (self.extra[self.EXTRA_PROBE_NAME], msg), kwargs


class Probe(abc.ABC):
    """Provides a unified interface for interacting with and testing a single Yagna node.

    This interface consists of several independent modules which may be extended
    in subclasses (see `ProviderProbe` and `RequestorProbe`).
    """

    runner: "Runner"
    """A runner that created this probe."""

    cli: YagnaDockerCli
    """A module which enables calling the Yagna CLI on the daemon being tested."""

    container: YagnaContainer
    """A module which handles the lifecycle of the daemon's Docker container."""

    ip_address: Optional[str]
    """An IP address of the daemon's container in the Docker network."""

    agent_logs: LogEventMonitor
    """Monitor and buffer for provider agent logs, enables asserting for certain lines
    to be present in the log buffer.
    """

    key_file: Optional[str]
    """Keyfile to be imported into the yagna daemon id service."""

    _last_checked_line: int
    """The index of the last line examined while waiting for log messages.

    Subsequent calls to `_wait_for_log()` will only look at lines that
    were logged after this line.
    """

    _docker_client: DockerClient
    """A docker client used to create the deamon's container."""

    def __init__(
        self,
        runner: "Runner",
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
    ):
        self.runner = runner
        self._docker_client = client
        self.container = YagnaContainer(client, config, log_config, assets_path)
        self.cli = Cli(self.container).yagna
        agent_log_config = LogConfig(
            file_name=f"{self.name}_agent",
            base_dir=self.container.log_config.base_dir,
        )
        # FIXME: Move agent logs to ProviderProbe when level0 is removed
        self.agent_logs = LogEventMonitor(agent_log_config)

        self._logger = ProbeLoggingAdapter(
            logger, {ProbeLoggingAdapter.EXTRA_PROBE_NAME: self.name}
        )
        self.ip_address = None
        self.key_file = config.key_file
        self._last_checked_line = -1

    def __str__(self):
        return self.name

    @property
    def address(self) -> Optional[str]:
        """Return address from id marked as default."""
        identity = self.cli.id_show()
        return identity.address if identity else None

    @property
    def app_key(self) -> Optional[str]:
        """Return first app key on the list."""
        keys = self.cli.app_key_list()
        return keys[0].key if keys else None

    @property
    def name(self) -> str:
        """Name of the container."""
        return self.container.name

    def start_container(self) -> None:
        """
        Start the probe's Docker container.

        Performs all necessary steps to make the daemon ready for testing
        (e.g. creating the default app key).
        """
        self.container.start()
        # Give the daemon some time to start before asking it for an app key.
        time.sleep(1)
        self.create_app_key()

        # Obtain the IP address of the container
        self.ip_address = get_container_address(
            self._docker_client, self.container.name
        )
        self._logger.info("IP address: %s", self.ip_address)

    def create_app_key(self, key_name: str = "test_key") -> str:
        """Attempt to create a new app key on the Yagna daemon.

        The key name can be specified via `key_name` parameter.
        Return the key as string.

        When `self.key_file` is set, this method also:
        - creates ID based on `self.key_file`
        - sets this new ID as default
        - restarts the container ( https://github.com/golemfactory/yagna/issues/458 )
        """
        address = None
        if self.key_file:
            self._logger.debug(
                "create_id(alias=%s, key_file=%s", key_name, self.key_file
            )
            try:
                db_id = self.cli.id_create(alias=key_name, key_file=self.key_file)
                address = db_id.address
                self._logger.debug("create_id. alias=%s, address=%s", db_id, address)
            except KeyAlreadyExistsError as e:
                logger.critical("Id already exists : (%r)", e)
                raise
                # db_id = next(
                #     filter(lambda i: i.id == e.TODO_extract_id(), self.cli.id_list())
                # )
                # address = db_id.address
            db_id = self.cli.id_update(address, set_default=True)
            self._logger.debug("update_id. result=%r", db_id)
            self.container.restart()
            time.sleep(1)
        try:
            key = self.cli.app_key_create(key_name)
            self._logger.debug("create_app_key. key_name=%s, key=%s", key_name, key)
        except KeyAlreadyExistsError:
            app_key = next(
                filter(lambda k: k.name == key_name, self.cli.app_key_list())
            )
            key = app_key.key
        return key

    @abc.abstractmethod
    def start_agent(self):
        """Start the agent."""

    async def stop(self):
        """
        Stop the probe, removing the Docker container of the daemon being tested.

        Once stopped, a probe cannot be restarted.
        """
        if self.container.logs:
            await self.container.logs.stop()
        await self.agent_logs.stop()
        self.container.remove(force=True)

    async def _wait_for_log(self, pattern: str, timeout: float = 1000) -> LogEvent:
        """Look for a log line with the message matching `pattern`."""

        regex = re.compile(pattern)

        def predicate(log_event) -> bool:
            return regex.match(log_event.message) is not None

        # First examine log lines already seen
        while self._last_checked_line + 1 < len(self.agent_logs.events):
            self._last_checked_line += 1
            event = self.agent_logs.events[self._last_checked_line]
            if predicate(event):
                return event

        # Otherwise create an assertion that waits for a matching line...
        async def coro(stream) -> LogEvent:
            try:
                log_event = await eventually(stream, predicate, timeout=timeout)
                return log_event
            finally:
                self._last_checked_line = len(stream.past_events) - 1

        assertion = self.agent_logs.add_assertion(coro)

        # ... and wait until the assertion completes
        while not assertion.done:
            await asyncio.sleep(0.1)

        if assertion.failed:
            raise assertion.result
        return assertion.result


# TODO: consider moving `start_agent()` to a separated mixin class, to make it clear
# that starting an agent does not depend on other optional features (API clients).
class RequestorProbe(Probe):
    """A probe subclass that can run a requestor agent.

    Can be used to select probes by role in a runner.
    Can be used in Level 0 scenarios.
    """

    def start_agent(self):
        """Start provider agent on the container and initialize its LogMonitor."""
        log_stream = self.container.exec_run(
            "ya-requestor"
            f" --app-key {self.app_key} --exe-script /asset/exe_script.json"
            " --task-package "
            "hash://sha3:d5e31b2eed628572a5898bf8c34447644bfc4b5130cfc1e4f10aeaa1:"
            "http://3.249.139.167:8000/rust-wasi-tutorial.zip",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)


class ProviderProbe(Probe):
    """A probe subclass that can run a provider agent.

    Can be used to select probes by role in a runner.
    Can be used in `ProbeStepBuilder`.
    """

    agent_preset: str
    """Name of the preset to be used when placing a market offer."""

    def __init__(
        self,
        runner: "Runner",
        client: DockerClient,
        config: YagnaContainerConfig,
        log_config: LogConfig,
        assets_path: Optional[Path] = None,
        preset_name: str = "default",
    ):
        super().__init__(runner, client, config, log_config, assets_path=assets_path)
        self.agent_preset = preset_name

    def start_agent(self):
        """Start the agent and attach the log monitor."""

        self.container.exec_run(
            f"ya-provider preset activate {self.agent_preset}",
        )
        log_stream = self.container.exec_run(
            f"ya-provider run" f" --app-key {self.app_key} --node-name {self.name}",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)


Provider = ProviderProbe
Requestor = RequestorProbe
Role = Type[Probe]
