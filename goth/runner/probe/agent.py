"""Module for agent components to be used with `Probe` objects."""
import abc
import logging
from typing import Optional, TYPE_CHECKING

from goth.runner.log import LogConfig
from goth.runner.log_monitor import LogEvent, LogEventMonitor
from goth.runner.probe.component import ProbeComponent

if TYPE_CHECKING:
    from goth.runner.probe import Probe

logger = logging.getLogger(__name__)


class AgentComponent(ProbeComponent, abc.ABC):
    """Probe component responsible for managing an agent binary.

    The agent can be an arbitrary binary executed in the container or on host.
    This class also includes logic for monitoring the agent logs and writing
    them to a file.
    """

    log_monitor: LogEventMonitor
    """Monitor and buffer for agent logs, enables asserting for certain lines to be
    present in the log buffer.
    """

    name: str
    """Name of this agent to be used when creating its log file.
    This should be unique when compared to other agents running as part of a
    single test. A good example includes both the probe's name, as well as the
    type of the agent itself, e.g.: `provider_1_ya-provider`.
    """

    def __init__(self, probe: "Probe", name: str):
        super().__init__(probe)
        self.name = name
        self._init_log_monitor()

    @abc.abstractmethod
    async def start(self, *args, **kwargs):
        """Start the agent binary and initialize the internal log monitor."""

    async def stop(self, *args, **kwargs):
        """Stop the agent binary and its log monitor."""
        if self.log_monitor:
            await self.log_monitor.stop()

    def _init_log_monitor(self):
        probe = self.probe
        log_config = LogConfig(file_name=self.name)

        if probe.container.log_config:
            log_config.base_dir = probe.container.log_config.base_dir

        self.log_monitor = LogEventMonitor(self.name, log_config)

    async def wait_for_log(
        self, pattern: str, timeout: Optional[float] = None
    ) -> LogEvent:
        """Search agent logs for a log line with the message matching `pattern`."""
        entry = await self.log_monitor.wait_for_entry(pattern, timeout)
        return entry


class ProviderAgentComponent(AgentComponent):
    """Probe component which runs `ya-provider` in the probe's container."""

    agent_preset: Optional[str]
    """Name of the preset to be used when placing a market offer."""

    subnet: str
    """Name of the subnet to which the provider agent connects."""

    def __init__(self, probe: "Probe", subnet: str, agent_preset: Optional[str] = None):
        super().__init__(probe, f"{probe.name}_ya-provider")
        self.agent_preset = agent_preset
        self.subnet = subnet

    async def start(self):
        """Start the provider agent and attach to its log stream."""
        await super().start()
        probe = self.probe
        probe._logger.info("Starting ya-provider")

        if self.agent_preset:
            probe.container.exec_run(f"ya-provider preset activate {self.agent_preset}")
        probe.container.exec_run(f"ya-provider config set --subnet {self.subnet}")

        log_stream = probe.container.exec_run(
            f"ya-provider run" f" --app-key {probe.app_key} --node-name {probe.name}",
            stream=True,
        )
        self.log_monitor.start(log_stream.output)
