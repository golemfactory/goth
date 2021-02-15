"""Classes and utilities to use a Monitor for log events."""

import asyncio
from datetime import datetime
from enum import Enum
import logging
import re
import time
from typing import Iterator, Optional, Sequence

from func_timeout.StoppableThread import StoppableThread

from goth.assertions.monitor import EventMonitor
from goth.assertions.operators import eventually
from goth.runner.exceptions import StopThreadException
from goth.runner.log import LogConfig

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Enum representing the rust log levels."""

    ERROR = 1
    WARN = 2
    INFO = 3
    DEBUG = 4
    TRACE = 5


# Pattern to match log lines from the `yagna` binary
pattern = re.compile(
    r"^\[(?P<datetime>[^ ]+) (?P<level>[^ ]+) (?P<module>[^\]]+)\] (?P<message>.*)"
)


class LogEvent:
    """An event representing a log line, used for asserting messages."""

    def __init__(self, log_message: str):
        self._timestamp = None
        self._level = None
        self._module = None
        self._message = log_message
        match = pattern.match(log_message)
        if match:
            result = match.groupdict()

            try:
                formatted_time = datetime.strptime(
                    result["datetime"], "%Y-%m-%dT%H:%M:%SZ"
                )
            except Exception:
                pass
            else:
                self._timestamp = formatted_time.timestamp()
                self._level = LogLevel[result["level"]]
                self._module = result["module"]
                self._message = result["message"]
        if not self._timestamp:
            self._timestamp = time.time()

    @property
    def timestamp(self) -> float:
        """Time of the log message.

        (or time of receiving the event when _module is None)
        """
        return self._timestamp

    @property
    def level(self) -> Optional[LogLevel]:
        """Level reported on the log message.

        Will be empty for multi line logs.
        """
        return self._level

    @property
    def module(self) -> Optional[str]:
        """Source module of this log message.

        Will be empty for multi line logs.
        """
        return self._module

    @property
    def message(self) -> str:
        """Text of the log message."""
        return self._message

    def __repr__(self):
        return (
            f"<LogEvent time={self.timestamp:0.0f}, level={self.level},"
            f" module={self.module}, message={self.message},  >"
        )


def _create_file_logger(config: LogConfig) -> logging.Logger:
    """Create a new file logger configured using the `LogConfig` object provided.

    The target log file will have a .log extension.
    """

    handler = logging.FileHandler(
        (config.base_dir / config.file_name).with_suffix(".log"),
        encoding="utf-8",
        delay=True,
    )
    handler.setFormatter(config.formatter)
    logger_ = logging.getLogger(str(config.file_name))
    logger_.setLevel(config.level)
    logger_.addHandler(handler)
    logger_.propagate = False
    return logger_


class LogEventMonitor(EventMonitor[LogEvent]):
    """Log buffer supporting logging to a file and waiting for a line pattern match.

    `log_config` parameter holds the configuration of the file logger.
    Consecutive values are interpreted as lines by splitting them on the new line
    character.
    Internally it uses an asyncio task to read the stream and add lines to the buffer.
    """

    _buffer_task: Optional[StoppableThread]
    _file_logger: logging.Logger
    _in_stream: Iterator[bytes]
    _last_checked_line: int
    """The index of the last line examined while waiting for log messages.

    Subsequent calls to `wait_for_agent_log()` will only look at lines that
    were logged after this line.
    """

    def __init__(self, log_config: LogConfig):
        super().__init__()
        self._file_logger = _create_file_logger(log_config)
        self._buffer_task = None
        self._last_checked_line = -1

    @property
    def events(self) -> Sequence[LogEvent]:
        """Return the events that occurred so far."""
        return self._events

    def start(self, in_stream: Iterator[bytes]):
        """Start reading the logs."""
        super().start()
        self.update_stream(in_stream)
        logger.debug("Started LogEventMonitor. name=%s", self._file_logger.name)

    async def stop(self) -> None:
        """Stop the monitor."""
        await super().stop()
        if self._buffer_task:
            self._buffer_task.stop(StopThreadException)

    def update_stream(self, in_stream: Iterator[bytes]):
        """Update the stream when restarting a container."""
        if self._buffer_task:
            self._buffer_task.stop(StopThreadException)
        self._in_stream = in_stream
        self._buffer_task = StoppableThread(target=self._buffer_input, daemon=True)
        self._buffer_task.start()

    def _buffer_input(self):
        try:
            for chunk in self._in_stream:
                chunk = chunk.decode()
                for line in chunk.splitlines():
                    self._file_logger.info(line)

                    event = LogEvent(line)
                    self.add_event(event)
        except StopThreadException:
            return

    async def wait_for_entry(self, pattern: str, timeout: float = 1000) -> LogEvent:
        """Search log for a log entry with the message matching `pattern`.

        The first call to this method will examine all log entries gathered
        since this monitor was started and then, if needed, will wait for
        up to `timeout` seconds for a matching entry.

        Subsequent calls will examine all log entries gathered since
        the previous call returned and then wait for up to `timeout` seconds.
        """
        regex = re.compile(pattern)

        def predicate(log_event) -> bool:
            return regex.match(log_event.message) is not None

        # First examine log lines already seen
        logger.debug("Checking past log lines. pattern=%s", pattern)
        while self._last_checked_line + 1 < len(self.events):
            self._last_checked_line += 1
            event = self.events[self._last_checked_line]
            if predicate(event):
                logger.debug(
                    "Found match in past log lines. pattern=%s, match=%s",
                    pattern,
                    event.message,
                )
                return event

        # Otherwise create an assertion that waits for a matching line...
        async def coro(stream) -> LogEvent:
            try:
                log_event = await eventually(stream, predicate, timeout=timeout)
                return log_event
            finally:
                self._last_checked_line = len(stream.past_events) - 1

        logger.debug("Creating log assertion. pattern=%s", pattern)
        assertion = self.add_assertion(coro)

        # ... and wait until the assertion completes
        while not assertion.done:
            await asyncio.sleep(0.1)

        result: LogEvent = await assertion.result()
        if result:
            logger.debug(
                "Log assertion completed with a match. pattern=%s, match=%s",
                pattern,
                result.message,
            )
        return result
