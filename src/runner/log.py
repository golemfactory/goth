import logging
import logging.config
from pathlib import Path

BASE_LOG_DIR = Path("/tmp/yagna_integration/")


LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "none": {"format": "%(message)s"},
        "console": {"format": "%(levelname)-8s [%(name)-35s] %(message)s"},
        "date": {
            "format": "%(asctime)s %(levelname)-8s %(name)-35s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "date",
            "filename": BASE_LOG_DIR / "integration.log",
            "encoding": "utf-8",
        },
        "console_agent": {
            "class": "logging.StreamHandler",
            "formatter": "none",
            "stream": "ext://sys.stdout",
        },
        "file_agent": {
            "class": "logging.FileHandler",
            "formatter": "none",
            "filename": BASE_LOG_DIR / "agent.log",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {"level": "INFO", "handlers": ["console", "file",],},
        "src.runner.node": {
            "level": "INFO",
            "handlers": ["console_agent", "file_agent"],
        },
    },
}


def configure_logging():
    BASE_LOG_DIR.mkdir(exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)
