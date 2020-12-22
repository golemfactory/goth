"""Module for adding yagna agent functionality to `Probe` subclasses."""
import abc
import logging

from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEvent, LogEventMonitor
from goth.runner.probe import Probe

logger = logging.getLogger(__name__)


class Agent(abc.ABC):
    """Mixin class which extends a `Probe` to allow for running an agent.

    The agent can be an arbitrary binary executed within the container. The abstract
    method `start_agent` is where this binary should be started.
    This mixin also includes logic for saving and monitoring the agent logs.
    """

    logs: LogEventMonitor
    """Monitor and buffer for agent logs, enables asserting for certain lines to be
    present in the log buffer.
    """

    _probe: Probe
    """Probe instance which contains this agent object."""

    @abc.abstractmethod
    async def start(self, **kwargs):
        """Start the probe and initialize the log monitor."""
        # self._init_log_monitor()

    @abc.abstractmethod
    async def stop(self):
        """Stop the probe and the log monitor."""
        # await self.logs.stop()

    async def wait_for_agent_log(self, pattern: str, timeout: float = 1000) -> LogEvent:
        """Search agent logs for a log line with the message matching `pattern`."""
        entry = await self.logs.wait_for_entry(pattern, timeout)
        return entry

    def _init_log_monitor(self):
        file_name = f"{self._probe.name}_agent"
        log_config = self._probe._container_config.log_config

        if log_config:
            log_config.file_name = file_name
        else:
            log_config = LogConfig(file_name=f"{self._probe.name}_agent")

        self.logs = LogEventMonitor(log_config)


class YaProviderAgent(Agent):
    """Stuff."""

    async def start(self, **kwargs):
        """Start the provider agent and attach to its log stream."""

        # TODO all of this depends on self.container, we need generic CLI

        if preset := kwargs.get('agent_preset'):
            self.container.exec_run(f"ya-provider preset activate {preset}")
        if subnet := kwargs.get('subnet'):
            self.container.exec_run(f"ya-provider config set --subnet {subnet}")

        log_stream = self.container.exec_run(
            f"ya-provider run"
            f" --app-key {self._probe.app_key} --node-name {self._probe.name}",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)

class YaRequestorAgent(Agent):
    """Stuff."""

    async def start(self, **kwargs):
        """Start the requestor agent and attach to its log stream."""

        # TODO proper asset handling, requires further refactoring

        pkg_spec = self.task_package.format(
            web_server_addr=self.runner.host_address,
            web_server_port=self.runner.web_server_port,
        )
        log_stream = self.container.exec_run(
            "ya-requestor"
            f" --app-key {self.app_key} --exe-script /asset/exe_script.json"
            f" --task-package {pkg_spec}",
            stream=True,
        )
        self.agent_logs.start(log_stream.output)

