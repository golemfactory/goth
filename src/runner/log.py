from datetime import datetime, timedelta
import logging
import logging.config
from pathlib import Path
import tempfile
from threading import Lock, Thread
import time
from typing import Iterator, List, Match, Optional, Pattern

BASE_LOG_DIR = Path(tempfile.gettempdir()) / "yagna-tests"


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
        "file_runner": {
            "class": "logging.FileHandler",
            "formatter": "date",
            "filename": BASE_LOG_DIR / "runner.log",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "src.runner": {"handlers": ["console"], "propagate": False},
        "src.runner.scenario": {"handlers": ["file_runner"]},
        "test_level0": {"handlers": ["console"], "propagate": False},
    },
}


def configure_logging():
    BASE_LOG_DIR.mkdir(exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)


def get_file_logger(file_name: str):
    """ Create a new logger that will output to a .log file with no formatting applied. """
    handler = logging.FileHandler(BASE_LOG_DIR / f"{file_name}.log", encoding="utf-8")
    formatter = logging.Formatter(fmt="%(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger(file_name)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


class LogBuffer:

    in_stream: Iterator[bytes]
    logger: logging.Logger

    def __init__(self, in_stream: Iterator[bytes], logger: logging.Logger):
        self.in_stream = in_stream
        self.logger = logger

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
