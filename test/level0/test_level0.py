import logging.config

from src.runner import Runner
from src.runner.log import configure_logging
from src.runner.scenario import Level0Scenario

configure_logging()


class TestLevel0:
    def test_level0(self):
        Runner().run(Level0Scenario())
