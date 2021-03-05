"""Module for adding yagna agent functionality to `Probe` subclasses."""
import abc
import logging

from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEvent, LogEventMonitor

logger = logging.getLogger(__name__)


class AgentMixin(abc.ABC):
    """Mixin class which extends a `Probe` to allow for running an agent.

    The agent can be an arbitrary binary executed within the container. The abstract
    method `start_agent` is where this binary should be started.
    This mixin also includes logic for saving and monitoring the agent logs.
    """

    agent_logs: LogEventMonitor
    """Monitor and buffer for agent logs, enables asserting for certain lines to be
    present in the log buffer.
    """

    @abc.abstractmethod
    def start_agent(self):
        """Start the agent binary.

        To enable the log monitor, this method must call `start` on `agent_logs`,
        passing in the log stream from the agent binary.
        """

    async def start(self):
        """Start the probe and initialize the log monitor."""
        self.agent_logs = None
        await super().start()
        self._init_log_monitor()

    async def stop(self):
        """Stop the probe and the log monitor."""
        await super().stop()
        if self.agent_logs:
            await self.agent_logs.stop()

    def _init_log_monitor(self):
        log_config = LogConfig(file_name=f"{self.name}_agent")
        if self.container.log_config:
            log_config.base_dir = self.container.log_config.base_dir

        self.agent_logs = LogEventMonitor(log_config)
        self._last_checked_line = -1

    async def _wait_for_agent_log(
        self, pattern: str, timeout: float = 1000
    ) -> LogEvent:
        """Search agent logs for a log line with the message matching `pattern`."""
        entry = await self.agent_logs.wait_for_entry(pattern, timeout)
        return entry
