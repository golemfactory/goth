import abc
from typing import Callable, List, Tuple

from src.runner.container import YagnaContainer
from src.runner.probe import Role


class Scenario(abc.ABC):
    @property
    @abc.abstractmethod
    def steps(self) -> List[Tuple[Callable, Role]]:
        """ List of steps to be executed as part of this test scenario. A single entry
            in the list is a tuple in which the first element is the function to be called
            and the second element specifies which nodes to run the function on. """

    @property
    @abc.abstractmethod
    def topology(self) -> List[YagnaContainer.Config]:
        """ List of container configurations to be used by the test runner when creating
            Docker containers for this scenario. """
