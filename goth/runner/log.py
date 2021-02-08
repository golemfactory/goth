"""Log utilities for the runner."""

from dataclasses import dataclass
import logging
import logging.config
from pathlib import Path
import tempfile
import time
from typing import Optional, Union

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
        "proxy_file": {
            "class": "logging.FileHandler",
            "formatter": "date",
            "filename": "%(base_log_dir)s/proxy.log",
            "encoding": "utf-8",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "goth.runner": {
            "handlers": ["console", "runner_file"],
            "propagate": False,
            "level": "DEBUG",
        },
        # This logger is used also by the assertions loaded into the proxy
        "goth.runner.proxy": {
            "handlers": ["proxy_file"],
            "propagate": True,
            "level": "DEBUG",
        },
        "goth.api_monitor": {
            "handlers": ["proxy_file"],
            "propagate": False,
            # Setting this to "DEBUG" can help in diagnosing issues with routing
            # in the proxy. Use "INFO" to avoid verbose logging of requests/responses.
            "level": "DEBUG",
        },
        "test.yagna.e2e": {
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
