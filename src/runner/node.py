from datetime import datetime, timedelta
from enum import Enum
import logging
from threading import Lock, Thread
import time
from typing import Iterator, List, Match, Optional, Pattern

from docker.models.containers import Container, ExecResult

from src.runner.cli import YagnaCli
from src.runner.exceptions import CommandError, TimeoutError
from src.runner.log import get_file_logger


logger = logging.getLogger(__name__)


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


class Role(Enum):
    requestor = 0
    provider = 1


class Node:
    def __init__(self, container: Container, role: Role):
        self.container = container
        self.cli = YagnaCli(container)
        self.logs = LogBuffer(
            container.logs(stream=True, follow=True), get_file_logger(self.name)
        )
        self.role = role

        self.agent_logs: LogBuffer

    def __str__(self):
        return self.name

    @property
    def address(self) -> Optional[str]:
        """ returns address from id marked as default """
        ids = self.cli.get_ids()
        default_id = next(filter(lambda i: i["default"] == "X", ids))
        return default_id["address"] if default_id else None

    @property
    def app_key(self) -> Optional[str]:
        """ returns first app key on the list """
        keys = self.cli.get_app_keys()
        return keys[0]["key"] if keys else None

    @property
    def name(self) -> str:
        return self.container.name

    def create_app_key(self, key_name: str) -> str:
        try:
            key = self.cli.create_app_key(key_name)
        except CommandError as e:
            if "UNIQUE constraint failed" in str(e):
                app_key: dict = next(
                    filter(lambda k: k["name"] == key_name, self.cli.get_app_keys())
                )
                key = app_key["key"]
        return key

    def start_provider_agent(self, preset_name: str):
        log_stream = self.container.exec_run(
            f"ya-provider run --app-key {self.app_key} --credit-address {self.address} --node-name {self.name} {preset_name}",
            stream=True,
        )
        self.agent_logs = LogBuffer(
            log_stream.output, get_file_logger(f"{self.name}_agent")
        )

    def start_requestor_agent(self):
        log_stream = self.container.exec_run(
            f"ya-requestor --app-key {self.app_key} --exe-script /asset/exe_script.json",
            stream=True,
        )
        self.agent_logs = LogBuffer(
            log_stream.output, get_file_logger(f"{self.name}_agent")
        )
