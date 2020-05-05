import logging
import logging.config
from pathlib import Path
import tempfile
import time

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
        "src.runner": {"handlers": ["console"], "propagate": False,},
        "src.runner.scenario": {"handlers": ["file_runner"]},
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
