"""Module with information on the project itself, e.g. project root directory."""
from pathlib import Path

import goth

PROJECT_ROOT = Path(goth.__file__).parent.parent
DEFAULT_ASSETS_DIR = PROJECT_ROOT / "goth" / "default-assets"
DOCKER_DIR = PROJECT_ROOT / "docker"
