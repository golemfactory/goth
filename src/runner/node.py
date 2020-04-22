from collections import deque
from datetime import datetime, timedelta
from enum import Enum
import logging
from queue import Empty, Queue
from threading import Lock, Thread
from typing import Deque, Iterator, List, Match, Optional, Pattern, Tuple

from docker.models.containers import Container, ExecResult

from src.runner.cli import YagnaCli
from src.runner.exceptions import CommandError, TimeoutError


logger = logging.getLogger(__name__)


class LogBuffer:
    def __init__(self, in_stream: Iterator[bytes]):
        self.in_stream = in_stream
        self._buffer: Deque[str] = deque()
        self._tail: Queue = Queue(maxsize=10)
        self._buffer_thread = Thread(target=self._buffer_input, daemon=True)
        self._buffer_thread.start()
        self._lock = Lock()

    def clear_buffer(self):
        self._buffer.clear()

    def search_for_pattern(self, pattern: Pattern[str]) -> Optional[Match[str]]:
        with self._lock:
            history = self._buffer.copy()

        # Reverse to search latest logs first
        for line in reversed(history):
            match = pattern.match(line)
            if match:
                return match

        return None

    def wait_for_pattern(
        self, pattern: Pattern[str], timeout: timedelta = timedelta(seconds=10)
    ) -> Match[str]:
        deadline = datetime.now() + timeout

        while deadline >= datetime.now():
            try:
                line = self._tail.get(timeout=timeout.seconds)
            except Empty:
                raise TimeoutError()

            match = pattern.match(line)
            if match:
                return match

        raise TimeoutError()

    def _buffer_input(self):
        for chunk in self.in_stream:
            chunk = chunk.decode()
            for line in chunk.splitlines():
                logger.info(line)
                # If _tail is full this will block until there's space available
                self._tail.put(line)

                with self._lock:
                    self._buffer.append(line)


class Role(Enum):
    requestor = 0
    provider = 1


class Node:
    def __init__(self, container: Container, role: Role):
        self.container = container
        self.cli = YagnaCli(container)
        self.logs = LogBuffer(container.logs(stream=True, follow=True))
        self.role = role

        self.agent_logs: LogBuffer

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

    def start_provider_agent(self, node_name: str, preset_name: str):
        log_stream = self.container.exec_run(
            f"ya-provider run --app-key {self.app_key} --credit-address {self.address} --node-name {node_name} {preset_name}",
            stream=True,
        )
        self.agent_logs = LogBuffer(log_stream.output)

    def start_requestor_agent(self):
        log_stream = self.container.exec_run(
            f"ya-requestor --app-key {self.app_key} --exe-script /asset/exe_script.json",
            stream=True,
        )
        self.agent_logs = LogBuffer(log_stream.output)
