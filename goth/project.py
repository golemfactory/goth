"""Module with information on the project itself, e.g. project root directory."""
from pathlib import Path

import goth

PROJECT_ROOT = Path(goth.__file__).parent.parent
DOCKER_DIR = PROJECT_ROOT / "docker"
TEST_DIR = PROJECT_ROOT / "test"
