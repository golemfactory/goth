"""Coroutine-based implementation of temporal assertions"""

import logging

from assertions.assertions import (
    Assertion,
    AssertionFunction,
    E,
    EventStream,
    TemporalAssertionError,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG
)

logger = logging.getLogger(__name__)
_file_handler = logging.FileHandler("assert.log", mode="a")
_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
logger.handlers = [_file_handler]
