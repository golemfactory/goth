from collections import deque
from copy import deepcopy
from datetime import datetime, timedelta
from enum import Enum
from queue import Queue
from threading import Thread
from typing import Deque, Iterator, List, Match, Optional, Pattern, Tuple

from docker.models.containers import Container, ExecResult

from runner.command import YagnaCli
from runner.exceptions import TimeoutError


class LogBuffer:
    def __init__(self, in_stream: Iterator[bytes]):
        self.in_stream = in_stream
        self._buffer: Deque[str] = deque()
        self._buffer_thread = Thread(target=self._buffer_input, daemon=True)
        self._buffer_thread.start()

    def clear_buffer(self):
        self._buffer.clear()

    def search_for_pattern(self, pattern: Pattern[str]) -> Optional[Match[str]]:
        logs = deepcopy(self._buffer)
        # Reverse to search latest logs first
        logs.reverse()
        for line in logs:
            match = pattern.match(line)
            if match:
                return match

        return None

    def wait_for_pattern(
        self, pattern: Pattern[str], timeout: timedelta
    ) -> Optional[Match[str]]:
        deadline = datetime.now() + timeout
        for line in self.in_stream:
            if deadline <= datetime.now():
                raise TimeoutError()
            match = pattern.match(line.decode())
            if match:
                return match

        return None

    def _buffer_input(self):
        for line in self.in_stream:
            self._buffer.append(line.decode())


class Role(Enum):
    requestor = 0
    provider = 1


class Node:
    def __init__(self, container: Container, role: Role):
        self.container = container
        self.cli = YagnaCli(container)
        self.logs = LogBuffer(container.logs(stream=True, follow=True))
        self.role = role

    @property
    def name(self) -> str:
        return self.container.name
