"""Assertion-related messages: utils for printing, parsing and JSON-enconding"""

from abc import ABC
from dataclasses import dataclass, asdict
import json
from typing import Optional


@dataclass(frozen=True)
class AssertionMessage(ABC):
    """Abstract base class for assertion messages"""

    assertion: str
    """Name of the assertion"""

    event_description: str
    """Description of the event to which this message refers, if any"""

    def as_json(self) -> str:
        """Encode `msg` as a dictionary and format it as a JSON string."""

        msg_dict = {"type": self.__class__.__name__, "fields": asdict(self)}
        return json.dumps(msg_dict)


@dataclass(frozen=True)
class AssertionStartMessage(AssertionMessage):
    """Message emitted when an assertion is started"""

    event_description: str = "assertion started"

    def __str__(self) -> str:
        return f"Assertion {self.assertion} started"


@dataclass(frozen=True)
class AssertionSuccessMessage(AssertionMessage):
    """Message emitted when an assertion succeeds"""

    result: str
    """Assertion result"""

    def __str__(self) -> str:
        return (
            f"Assertion {self.assertion} succeeded after {self.event_description}"
            f", result: {self.result}"
        )


@dataclass(frozen=True)
class AssertionFailureMessage(AssertionMessage):
    """Message emitted when an assertion fails"""

    cause: str
    """Cause of the failure"""

    def __str__(self) -> str:
        return (
            f"Assertion {self.assertion} failed after {self.event_description}"
            f", cause: {self.cause}"
        )


msg_classes = {
    cls.__name__: cls
    for cls in (AssertionFailureMessage, AssertionStartMessage, AssertionSuccessMessage)
}


def parse_assertion_message(text: str) -> Optional[AssertionMessage]:
    """If `text` is a JSON-encoded assertion message then parse and
    return the message. Otherwise, return `None`.
    """

    try:
        msg_dict = json.loads(text)
        fields = msg_dict["fields"]
        cls = msg_classes[msg_dict["type"]]
        return cls(**fields)
    except (json.decoder.JSONDecodeError, KeyError, TypeError):
        return None
