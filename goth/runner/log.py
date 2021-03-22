"""Log utilities for the runner."""

import contextlib
from dataclasses import dataclass
import logging
import logging.config
from pathlib import Path
import tempfile
import time
from typing import Iterator, Optional, Union

import goth
import goth.api_monitor
from goth.assertions.monitor import EventMonitor


DEFAULT_LOG_DIR = Path(tempfile.gettempdir()) / "goth-tests"
FORMATTER_NONE = logging.Formatter("%(message)s")

logger = logging.getLogger(__name__)


class UTCFormatter(logging.Formatter):
    """Custom `logging` formatter that uses `time.gmtime`."""

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
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",
        },
        "runner_file": {
            "class": "logging.FileHandler",
            "formatter": "date",
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
        formatter = logging.Formatter(
            fmt=LOGGING_CONFIG["formatters"]["date"]["format"],
            datefmt=LOGGING_CONFIG["formatters"]["date"]["datefmt"],
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


class MonitorHandler(logging.Handler):
    """A logging handler that passes messages from log records to an event monitor."""

    def __init__(self, monitor: EventMonitor[str]):
        self._monitor = monitor
        super().__init__()

    def handle(self, record: logging.LogRecord) -> None:
        """Add the `record`'s message to the associated event monitor."""
        self._monitor.add_event_sync(record.getMessage())


@contextlib.contextmanager
def monitored_logger(name: str, monitor: EventMonitor[str]) -> Iterator[logging.Logger]:
    """Get logger identified by `name` and attach the given event monitor to it.

    The monitor will receive all messages emitted by the logger as events.
    Upon exiting from this context manager, the monitor will be detached
    from the logger.
    """

    logger_ = logging.getLogger(name)
    handler = MonitorHandler(monitor)
    try:
        logger_.addHandler(handler)
        yield logger_
    finally:
        if handler in logger_.handlers:
            logger_.removeHandler(handler)
