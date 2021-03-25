"""Classes and utilities to use a Monitor for log events."""

import asyncio
from datetime import datetime
from enum import Enum
import logging
import re
import time
from typing import Iterator, Optional, Sequence

from func_timeout.StoppableThread import StoppableThread

from goth.assertions.monitor import E, EventMonitor
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
    logger_name = f"{config.base_dir}.{config.file_name}"
    logger_ = logging.getLogger(logger_name)
    logger_.setLevel(config.level)
    logger_.addHandler(handler)
    logger_.propagate = False
    return logger_


class PatternMatchingEventMonitor(EventMonitor[E]):
    """An `EventMonitor` that can wait for events that match regex patterns."""

    def event_str(self, event: E) -> str:
        """Return the string associated with `event` on which to perform matching."""
        return str(event)

    async def wait_for_pattern(
        self, pattern: str, timeout: Optional[float] = None
    ) -> E:
        """Wait for an event with string representation matching `pattern`.

        The semantics for this method is as for
        `EventMonitor.wait_for_event(predicate, timeout)`, with `predicate(e)`
        being true iff `event_str(e)` matches `pattern`, for any event `e`.
        """

        regex = re.compile(pattern)
        event = await self.wait_for_event(
            lambda e: regex.match(self.event_str(e)) is not None, timeout
        )
        return event


class LogEventMonitor(PatternMatchingEventMonitor[LogEvent]):
    """Log buffer supporting logging to a file and waiting for a line pattern match.

    `log_config` parameter holds the configuration of the file logger.
    Consecutive values are interpreted as lines by splitting them on the new line
    character.
    Internally it uses a thread to read the stream and add lines to the buffer.
    """

    _buffer_task: Optional[StoppableThread]
    _file_logger: logging.Logger
    _in_stream: Iterator[bytes]

    def __init__(self, name: str, log_config: Optional[LogConfig] = None):
        super().__init__(name)
        if log_config:
            self._file_logger = _create_file_logger(log_config)
        else:
            self._file_logger = logging.getLogger(name)
        self._buffer_task = None
        self._loop = asyncio.get_event_loop()

    def event_str(self, event: LogEvent) -> str:
        """Return the string associated with `event` on which to perform matching."""
        return event.message

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
                    self.add_event_sync(event)

        except StopThreadException:
            return

    async def wait_for_entry(
        self, pattern: str, timeout: Optional[float] = None
    ) -> LogEvent:
        """Search log for a log entry with the message matching `pattern`.

        The first call to this method will examine all log entries gathered
        since this monitor was started and then, if needed, will wait for
        up to `timeout` seconds (or indefinitely, if `timeout` is `None`)
        for a matching entry.

        Subsequent calls will examine all log entries gathered since
        the previous call returned and then wait for up to `timeout` seconds.
        """
        event = await self.wait_for_pattern(pattern, timeout)
        logger.debug(
            "Log assertion completed with a match. pattern=%s, match=%s",
            pattern,
            event.message,
        )
        return event
