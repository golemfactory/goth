import abc
from typing import Callable, Dict, List, Tuple

from src.runner.probe import Role


class Scenario(abc.ABC):
    @property
    @abc.abstractmethod
    def nodes(self) -> Dict[Role, int]:
        """ Defines what nodes should be started before the test scenario is run.
            Keys in the dictionary are node roles, values are counts of instances
            to be started. """

    @property
    @abc.abstractmethod
    def steps(self) -> List[Tuple[Callable, Role]]:
        """ List of steps to be executed as part of this test scenario. A single entry
            in the list is a tuple in which the first element is the function to be called
            and the second element specifies which nodes to run the function on. """
