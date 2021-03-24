"""Unit tests for probe agents."""

from unittest.mock import MagicMock

from goth.runner.probe import Probe
from goth.runner.probe.agent import AgentComponent


def test_agent_duplicate_names():
    """Test if two agent objects with the same name will be treated as equal."""

    class TestAgentComponent(AgentComponent):
        pass

    agents = set()
    agent_name = "test_agent"
    probe = MagicMock(spec=Probe)

    first_agent = TestAgentComponent(probe, agent_name)
    agents.add(first_agent)
    agents.add(TestAgentComponent(probe, agent_name))

    assert len(agents) == 1
    assert agents.pop() == first_agent


def test_agent_different_names():
    """Test if two agent objects with different names will be treated as different."""

    class TestAgentComponent(AgentComponent):
        pass

    agents = set()
    probe = MagicMock(spec=Probe)

    agents.add(TestAgentComponent(probe, "agent_1"))
    agents.add(TestAgentComponent(probe, "agent_2"))

    assert len(agents) == 2
