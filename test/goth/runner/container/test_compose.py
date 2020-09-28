"""Test the `runner.container.compose` module."""
from goth.runner.container.compose import get_compose_services

EXPECTED_SERVICES = ["ethereum", "mock-api", "proxy-nginx", "router"]


def test_get_compose_services():
    """Test whether the services in docker-compose.yml match the expected ones."""
    services = get_compose_services()
    for service in EXPECTED_SERVICES:
        assert service in services
