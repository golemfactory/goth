"""Module with information on the project itself, e.g. project root directory."""
from pathlib import Path

import goth


def _find_parent_with(start: Path, child_name: str):
    """Walk filesystem upwards from `start` looking for dir containing `child_name`.

    Return first dir with item named `child_name` or None if no matches were found.
    """
    parents = start.resolve().parents
    to_visit = [start] + list(parents)

    for current in to_visit:
        current = current.resolve()
        for child in current.iterdir():
            if child.name == child_name:
                return current

    return None


PROJECT_ROOT = _find_parent_with(Path(goth.__file__).parent, ".git")
DOCKER_DIR = PROJECT_ROOT / "docker"
