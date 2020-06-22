""" Log utilities for the runner"""
from dataclasses import dataclass
import logging
import logging.config
from pathlib import Path
import tempfile
import time
from typing import Union

DEFAULT_LOG_DIR = Path(tempfile.gettempdir()) / "yagna-tests"
FORMATTER_NONE = logging.Formatter("%(message)s")

logger = logging.getLogger(__name__)


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


def configure_logging(base_dir: Path = DEFAULT_LOG_DIR):
    """ Configure the `logging` module. Updates config with `base_dir` before
    applying the global configuration  """

    # substitute `base_log_dir` in `LOGGING_CONFIG` with the actual dir path
    for _name, handler in LOGGING_CONFIG["handlers"].items():
        if "filename" in handler:
            # format the handler's filename with the base dir
            handler["filename"] %= {"base_log_dir": str(base_dir)}

    base_dir.mkdir(exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info("started logging. dir=%s", base_dir)


@dataclass
class LogConfig:
    """ Configuration used to create file loggers.  """

    file_name: Union[str, Path]
    base_dir: Path = DEFAULT_LOG_DIR
    formatter: logging.Formatter = FORMATTER_NONE
    level: int = logging.INFO
