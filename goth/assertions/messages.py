"""Assertion-related messages: utils for printing, parsing and JSON-enconding"""

from abc import abstractmethod
from dataclasses import dataclass, asdict
import json
from typing import Optional


@dataclass(frozen=True)
class AssertionMessage:
    """Abstract base class for assertion messages"""

    assertion: str
    """Name of the assertion"""

    event_description: str
    """Description of the event to which this message refers, if any"""

    @abstractmethod
    def pretty(self) -> str:
        """Return a human-readable description of this message."""


@dataclass(frozen=True)
class AssertionStartMessage(AssertionMessage):
    """Message emitted when an assertion is started"""

    event_description: str = "assertion started"

    def pretty(self) -> str:
        return f"Assertion {self.assertion} started"


@dataclass(frozen=True)
class AssertionSuccessMessage(AssertionMessage):
    """Message emitted when an assertion succeeds"""

    result: str
    """Assertion result"""

    def pretty(self) -> str:
        return (
            f"Assertion {self.assertion} succeeded after {self.event_description}"
            f", result: {self.result}"
        )


@dataclass(frozen=True)
class AssertionFailureMessage(AssertionMessage):
    """Message emitted when an assertion fails"""

    cause: str
    """Cause of the failure"""

    def pretty(self) -> str:
        return (
            f"Assertion {self.assertion} failed after {self.event_description}"
            f", cause: {self.cause}"
        )


def format_assertion_message(msg: AssertionMessage) -> str:
    """Encode `msg` as a dictionary and format it as JSON string."""

    msg_dict = {"type": msg.__class__.__name__, "fields": asdict(msg)}
    return json.dumps(msg_dict)


msg_classes = {
    cls.__name__: cls
    for cls in (AssertionFailureMessage, AssertionStartMessage, AssertionSuccessMessage)
}


def parse_assertion_message(text: str) -> Optional[AssertionMessage]:
    """Parse JSON-encoded message."""

    try:
        msg_dict = json.loads(text)
        fields = msg_dict["fields"]
        cls = msg_classes[msg_dict["type"]]
        return cls(**fields)
    except (json.decoder.JSONDecodeError, KeyError, TypeError):
        return None
