"""Code common for all pytest modules in this package"""
import contextlib
import logging
import time

import docker
import pytest

from src.runner.exceptions import CommandError


logger = logging.getLogger(__name__)


@pytest.fixture(scope="package")
def yagna_container():
    """A fixture for starting and terminating a container using the `yagna` image"""

    client = docker.from_env()
    container = client.containers.run(
        "yagna", entrypoint=["bin/sh"], detach=True, tty=True,
    )
    while container.status != "running":
        logger.debug("Waiting for the container...")
        time.sleep(1)
        container.reload()

    logger.info("Yagna container started")
    yield container

    # Cleanup code run when the fixture goes out of scope
    container.stop()
    container.remove()
    logger.info("Yagna container removed")


@contextlib.contextmanager
def yagna_daemon_running(container, data_dir=None):
    """Start a yagna daemon using a random data dir; kill the daemon on exit."""

    if not data_dir:
        result = container.exec_run("mktemp -d")
        if result.exit_code != 0:
            raise CommandError("Cannot mktemp -d")
        data_dir = result.output.decode().strip()

    result = container.exec_run(f"yagna service run -d {data_dir}", detach=True)
    # exit_code should be None since we detached from the command
    if result.exit_code is not None:
        raise CommandError(f"Cannot start yagna daemon: {result.output}")

    logger.debug("Yagna daemon started, data dir: %s", data_dir)

    result = container.exec_run("ps x")
    if result.exit_code != 0:
        raise CommandError(f"Cannot run `ps x`: {result.output}")

    pid = None
    for line in result.output.decode().split("\n"):
        if "yagna service run" in line:
            pid = int(line.split()[0])
            break

    if pid is None:
        raise CommandError("Yagna daemon doesn't appear to be running")

    yield pid

    result = container.exec_run(f"kill {pid}")
    if result.exit_code != 0:
        raise CommandError(f"Cannot kill yagna daemon: {result.output}")

    logging.debug("Yagna daemon killed")
