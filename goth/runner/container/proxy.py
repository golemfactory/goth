import logging
from pathlib import Path
from typing import Iterator, Optional

from docker import DockerClient

from goth.assertions import EventStream
from goth.assertions.messages import AssertionFailureMessage, parse_assertion_message
from goth.runner.log_monitor import LogEvent
from goth.runner.container import DockerContainer, DockerContainerConfig
from goth.runner.log_monitor import LogConfig, LogEventMonitor


logger = logging.getLogger(__name__)


class ProxyContainerConfig(DockerContainerConfig):
    """Configuration for a proxy container"""


class ProxyContainer(DockerContainer):
    """A `DockerContainer` subclass for running mitmproxy nodes as part of test setup"""

    IMAGE = "api-monitor"
    ENTRYPOINT = "./start-proxy.sh"

    def __init__(
        self,
        client: DockerClient,
        config: ProxyContainerConfig,
        log_config: Optional[LogConfig] = None,
        assets_path: Optional[Path] = None,
        **kwargs,
    ):
        super().__init__(
            client,
            command=[],
            entrypoint=self.ENTRYPOINT,
            image=self.IMAGE,
            log_config=log_config,
            name=config.name,
            environment={},
            ports={},
            volumes=config.get_volumes_spec(assets_path) if assets_path else {},
            hostname=config.name,
            **kwargs,
        )

    def _create_log_monitor(self):
        return ProxyLogMonitor(
            self._container.logs(stream=True, follow=True),
            self.log_config,
            node_name=self.name,
        )


class ProxyLogMonitor(LogEventMonitor):
    """A `LogEventMonitor` subclass that detects assertion messages in observed
    logs and raises `AssertionExceptions` on assertion failure messages.
    """

    node_name: str

    def __init__(
        self, in_stream: Iterator[bytes], log_config: LogConfig, node_name: str
    ):
        super().__init__(in_stream, log_config)
        self.node_name = node_name

    async def _detect_assertion_failures(self, stream: EventStream[LogEvent]):

        async for event in stream:

            msg = parse_assertion_message(event.message)
            if isinstance(msg, AssertionFailureMessage):
                logger.error("API error in '%s': %s", self.node_name, msg)
                raise AssertionError(msg)

    def start(self) -> None:
        """Overrides `EventMonitor.start()`."""

        super(ProxyLogMonitor, self).start()
        self.add_assertions([self._detect_assertion_failures])

    def _log_line(self, line: str) -> None:
        """Overrides `LogEventMonitor._log_line()`: lines with assertion messages
        are not logged.
        """

        if not parse_assertion_message(line):
            self.logger.info(line)
