from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import logging.config
from pathlib import Path
import tempfile
from threading import Lock, Thread
import time
from typing import Iterator, List, Match, Optional, Pattern, Union

DEFAULT_LOG_DIR = Path(tempfile.gettempdir()) / "yagna-tests"
FORMATTER_NONE = logging.Formatter("%(message)s")


class UTCFormatter(logging.Formatter):
    converter = time.gmtime


LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "none": {"format": "%(message)s"},
        "simple": {"format": "%(levelname)-8s [%(name)-30s] %(message)s"},
        "date": {
            "()": UTCFormatter,
            "format": "%(asctime)s %(levelname)-8s %(name)-30s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S%z",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple",},
        "runner_file": {
            "class": "logging.FileHandler",
            "formatter": "date",
            "filename": "%(base_log_dir)s/runner.log",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "src.runner": {"handlers": ["console", "runner_file"], "propagate": False},
        "test_level0": {"handlers": ["console", "runner_file"], "propagate": False},
        "transitions": {"level": "WARNING"},
    },
}


def configure_logging(base_dir: Optional[Path]):
    # substitute `base_log_dir` in `LOGGING_CONFIG` with the actual dir path
    for _name, handler in LOGGING_CONFIG["handlers"].items():
        if "filename" in handler:
            # format the handler's filename with the base dir
            handler["filename"] %= {"base_log_dir": str(base_dir)}

    (base_dir or DEFAULT_LOG_DIR).mkdir(exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)


@dataclass
class LogConfig:
    """ Configuration used to create file loggers.  """

    file_name: Union[str, Path]
    base_dir: Path = DEFAULT_LOG_DIR
    formatter: logging.Formatter = FORMATTER_NONE
    level: int = logging.INFO


def _create_file_logger(config: LogConfig) -> logging.Logger:
    """ Create a new file logger configured using the `LogConfig` object provided.
        The target log file will have a .log extension. """
    handler = logging.FileHandler(
        (config.base_dir / config.file_name).with_suffix(".log"), encoding="utf-8"
    )
    handler.setFormatter(config.formatter)
    logger = logging.getLogger(str(config.file_name))
    logger.setLevel(config.level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


class LogBuffer:
    """ Buffers logs coming from `in_stream`. Consecutive values are interpreted as lines
        by splitting them on the new line character. Internally, it uses a daemon thread
        to read the stream and add lines to the buffer. """

    in_stream: Iterator[bytes]
    logger: logging.Logger

    def __init__(self, in_stream: Iterator[bytes], log_config: LogConfig):
        self.in_stream = in_stream
        self.logger = _create_file_logger(log_config)

        self._buffer: List[str] = []
        # Index of last line read from the buffer using `wait_for_pattern`
        self._last_read: int = -1
        self._buffer_thread = Thread(target=self._buffer_input, daemon=True)
        self._lock = Lock()

        self._buffer_thread.start()

    def clear_buffer(self):
        self._buffer.clear()
        self._last_read = -1

    def search_for_pattern(
        self, pattern: Pattern[str], entire_buffer: bool = False
    ) -> Optional[Match[str]]:
        """ Search the buffer for a line matching the given pattern.
            By default, this searches only the lines which haven't been read yet.
            :param bool entire_buffer: when True, the entire available buffer will be searched.
            :return: Match[str] object if a matching line is found, None otherwise. """
        with self._lock:
            history = self._buffer.copy()

        if not entire_buffer:
            # This will yield an empty list if there are no unread lines
            history = history[self._last_read + 1 :]
        self._last_read = len(self._buffer) - 1

        # Reverse to search latest logs first
        for line in reversed(history):
            match = pattern.match(line)
            if match:
                return match

        return None

    def wait_for_pattern(
        self, pattern: Pattern[str], timeout: timedelta = timedelta(seconds=10)
    ) -> Match[str]:
        """ Blocking call which waits for a matching line to appear in the buffer.
            This tests all the unread lines in the buffer before waiting for
            new lines to appear.
            :param timedelta timeout: the maximum time to wait for a matching line.
            :raises TimeoutError: if the timeout is reached with no match."""
        deadline = datetime.now() + timeout

        while deadline >= datetime.now():
            # Check if there are new lines available in the buffer
            if len(self._buffer) > self._last_read + 1:
                self._last_read += 1
                next_line = self._buffer[self._last_read]
                match = pattern.match(next_line)
                if match:
                    return match
            else:
                # Prevent busy waiting
                time.sleep(0.1)

        raise TimeoutError()

    def _buffer_input(self):
        for chunk in self.in_stream:
            chunk = chunk.decode()
            for line in chunk.splitlines():
                self.logger.info(line)

                with self._lock:
                    self._buffer.append(line)
