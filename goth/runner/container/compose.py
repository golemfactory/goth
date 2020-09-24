"""Module responsible for parsing the docker-compose.yml used in the tests."""

import yaml

from goth.project import DOCKER_DIR

COMPOSE_FILE = DOCKER_DIR / "docker-compose.yml"


def get_compose_services() -> dict:
    """Return services defined in docker-compose.yml.

    These correspond to the static containers running for each test.
    """
    with COMPOSE_FILE.open() as f:
        return yaml.safe_load(f)["services"]
