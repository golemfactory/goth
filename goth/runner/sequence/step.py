"""Defines the `Step` class used in test scenarios."""
import abc
import asyncio
import logging
from typing import Any, Callable, List

from goth.assertions import Assertion
from goth.runner import Probe


logger = logging.getLogger(__name__)


class Step(abc.ABC):
    """Step to be awaited in the runner."""

    def __init__(self, name: str, timeout: int):
        self.name = name
        self.timeout = timeout

    @abc.abstractmethod
    async def tick(self):
        """Wait until this step is complete.

        Implemented in sub-classes of Step
        """

    def __str__(self):
        return f"{self.name}(timeout={self.timeout})"

    def __repr__(self):
        return f"<{type(self).__name__} name={self.name} timeout={self.timeout}>"


class AssertionStep(Step):
    """Step that holds a set of assertions to await."""

    assertions: List[Assertion]
    """All assertions that have to pass for this step."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assertions = []

    def add_assertion(self, assertion: Assertion):
        """Add an assertion to be awaited in this step."""
        self.assertions.append(assertion)

    async def tick(self) -> bool:
        """Handle required action and return `True` iff this step has been completed.

        For the AssertionStep this means all assertions are marked as done.
        """
        while not all(a.done for a in self.assertions):
            await asyncio.sleep(0.1)
        return True


class CallableStep(Step):
    """Step that executes a python function call on all `probes`."""

    probes: List[Probe]
    """Probes to execute `callable(probe)` for."""
    callback: Callable[[Probe], Any]
    """Callable to be executed for each probe when the step is ticked"""

    def __init__(
        self,
        name: str,
        timeout: int,
        probes: List[Probe],
        callback: Callable[[Probe], Any],
    ):
        super().__init__(name, timeout)
        self.probes = probes
        self.callback = callback

    async def tick(self) -> bool:
        """Handle required action and return `True` iff this step has been completed.

        For the CallableStep this means the callback is executed for each probe.
        """
        for probe in self.probes:
            res = self.callback(probe)
            logger.debug("step=%s, probe=%s result=%r", self, probe, res)
            # Sleep to allow other asyncio Tasks to continue
            await asyncio.sleep(0.0)
        return True
