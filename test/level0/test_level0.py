from pathlib import Path

from src.runner import Runner
from src.runner.scenario import Level0Scenario


class TestLevel0:
    def test_level0(self, assets_path: Path):
        Runner(assets_path).run(Level0Scenario())
