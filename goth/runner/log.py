"""Log utilities for the runner."""

import contextlib
from dataclasses import dataclass
import logging
import logging.config
from pathlib import Path
import tempfile
import time
from typing import Iterator, Optional, Union

import colors

import goth
import goth.api_monitor
from goth.assertions.monitor import EventMonitor


DEFAULT_LOG_DIR = Path(tempfile.gettempdir()) / "goth-tests"
FORMATTER_NONE = logging.Formatter("%(message)s")

logger = logging.getLogger(__name__)


class CustomFileLogFormatter(logging.Formatter):
    """`Formatter` that uses `time.gmtime` for time and strips ANSI color codes."""

    converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        """Format the message and remove ANSI color codes from it."""
        text = super().format(record)
        return colors.strip_color(text)


LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "none": {"format": "%(message)s"},
        "console": {"format": "%(levelname)-8s [%(name)-30s] %(message)s"},
        "file": {
            "()": CustomFileLogFormatter,
            "format": "%(asctime)s %(levelname)-8s %(name)-30s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S%z",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "level": "INFO",
        },
        "runner_file": {
            "class": "logging.FileHandler",
            "formatter": "file",
            "filename": "%(base_log_dir)s/runner.log",
            "encoding": "utf-8",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "goth": {
            "handlers": ["console", "runner_file"],
            "propagate": False,
            "level": "DEBUG",
        },
        "goth.api_monitor": {
            "handlers": [],
            "propagate": False,
            # Setting this to "DEBUG" can help in diagnosing issues with routing
            # in the proxy. Use "INFO" to avoid verbose logging of requests/responses.
            "level": "DEBUG",
        },
        "test.yagna": {
            "handlers": ["console", "runner_file"],
            "propagate": False,
            "level": "DEBUG",
        },
        "aiohttp": {
            "handlers": ["console", "runner_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "transitions": {"level": "WARNING"},
    },
}


def configure_logging(base_dir: Path, console_log_level: Optional[str] = None) -> None:
    """Configure the `logging` module.

    Updates config with `base_dir` before applying the global configuration.
    """

    # substitute `base_log_dir` in `LOGGING_CONFIG` with the actual dir path
    for _name, handler in LOGGING_CONFIG["handlers"].items():
        if "filename" in handler:
            # format the handler's filename with the base dir
            handler["filename"] %= {"base_log_dir": str(base_dir)}

    if console_log_level:
        LOGGING_CONFIG["handlers"]["console"]["level"] = console_log_level

    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info("started logging. dir=%s", base_dir)


@dataclass
class LogConfig:
    """Configuration used to create file loggers."""

    file_name: Union[str, Path]
    base_dir: Path = DEFAULT_LOG_DIR
    formatter: logging.Formatter = FORMATTER_NONE
    level: int = logging.INFO


@contextlib.contextmanager
def configure_logging_for_test(test_log_dir: Path) -> None:
    """Configure loggers to write to files in `test_log_dir`.

    Implements context manager protocol: on entering the context file handlers
    will be added to certain loggers; on exiting these handlers will be removed.
    """

    goth_logger = logging.getLogger(goth.__name__)
    api_monitor_logger = logging.getLogger(goth.api_monitor.__name__)

    runner_handler = None
    proxy_handler = None

    try:
        formatter = CustomFileLogFormatter(
            fmt=LOGGING_CONFIG["formatters"]["file"]["format"],
            datefmt=LOGGING_CONFIG["formatters"]["file"]["datefmt"],
        )

        # TODO: ensure the new files created here do not conflict with probe logs
        runner_handler = logging.FileHandler(str(test_log_dir / "test.log"))
        runner_handler.setLevel(logging.DEBUG)
        runner_handler.setFormatter(formatter)
        goth_logger.addHandler(runner_handler)

        proxy_handler = logging.FileHandler(str(test_log_dir / "proxy.log"))
        proxy_handler.setLevel(logging.DEBUG)
        proxy_handler.setFormatter(formatter)
        api_monitor_logger.addHandler(proxy_handler)

        yield

    finally:
        if runner_handler in goth_logger.handlers:
            goth_logger.handlers.remove(runner_handler)
        if proxy_handler in api_monitor_logger.handlers:
            api_monitor_logger.handlers.remove(proxy_handler)


class MonitoringFilter(logging.Filter):
    """A logging `Filter` that feeds messages to the underlying event monitor.

    After doing this it also adds some color to the messages for greater fun.
    """

    def __init__(self, monitor: EventMonitor[str], color: Optional[str] = None):
        super().__init__()
        self._monitor: EventMonitor[str] = monitor
        self._color: Optional[str] = color

    def filter(self, record: logging.LogRecord) -> bool:
        """Pass the record's message to the monitor, add colors to the message."""
        message = record.getMessage()
        self._monitor.add_event_sync(message)
        if self._color:
            record.msg = colors.color(message, fg=self._color)
        record.args = ()
        return True


@contextlib.contextmanager
def monitored_logger(name: str, monitor: EventMonitor[str]) -> Iterator[logging.Logger]:
    """Get logger identified by `name` and attach the given event monitor to it.

    The monitor will receive all messages emitted by the logger as events.
    Upon exiting from this context manager, the monitor will be detached
    from the logger.
    """

    logger_to_monitor = logging.getLogger(name)
    filter = MonitoringFilter(monitor, "cyan")
    logger_to_monitor.filters.insert(0, filter)
    try:
        yield logger_to_monitor
    finally:
        logger_to_monitor.removeFilter(filter)
