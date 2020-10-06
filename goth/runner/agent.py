"""Module for adding yagna agent functionality to `Probe` subclasses."""
import abc
import asyncio
import logging
import re

from goth.assertions.operators import eventually
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

    _last_checked_line: int
    """The index of the last line examined while waiting for log messages.

    Subsequent calls to `wait_for_agent_log()` will only look at lines that
    were logged after this line.
    """

    @abc.abstractmethod
    def start_agent(self):
        """Start the agent binary.

        To enable the log monitor, this method must call `start` on `agent_logs`,
        passing in the log stream from the agent binary.
        """

    def start(self):
        """Start the probe and initialize the log monitor."""
        super().start()
        self._init_log_monitor()

    async def stop(self):
        """Stop the probe and the log monitor."""
        await super().stop()
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
