"""Module containing the base class for probe components."""

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from goth.runner.probe import Probe


class ProbeComponent(abc.ABC):
    """Base class for a probe component.

    This serves as a common interface for all classes which can be part of the `Probe`
    class (as in: composition over inheritance).
    """

    def __init__(self, probe: "Probe"):
        self.probe = probe

    probe: "Probe"
    """Probe instance containing this component."""
