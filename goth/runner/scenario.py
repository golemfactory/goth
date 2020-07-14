"""Abstract classes for Topology and Scenario. To be used by `Runner`."""

import abc
from typing import Awaitable, Callable, List, Optional, Tuple

from goth.runner.container import DockerContainerConfig
from goth.runner.probe import Role

StepFunction = Callable[..., Optional[Awaitable]]


class Scenario(abc.ABC):
    """Abstract template for required properties on a Scenario."""

    @property
    @abc.abstractmethod
    def steps(self) -> List[Tuple[StepFunction, Role]]:
        """List of steps to be executed as part of this test scenario.

        A single entry in the list is a tuple in which the first element is the function
        to be called and the second element specifies which nodes to run the function
        on.
        """

    @property
    @abc.abstractmethod
    def topology(self) -> List[DockerContainerConfig]:
        """List of container configurations to be used by the test runner.

        when creating Docker containers for this scenario.
        """

    @property
    @abc.abstractmethod
    def api_assertions_module(self) -> str:
        """Name of the assertions module that should be loaded into the API monitor.

        The name should be relative to the directory containing the scenario module.
        """
