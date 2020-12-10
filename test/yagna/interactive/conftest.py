"""Pytest fixtures for running test harness in interactive mode."""

import logging
from pathlib import Path
from typing import Callable

import pytest

from goth.runner import TestFailure


logger = logging.getLogger("goth.runner.interactive")


@pytest.fixture(scope="module")
def assets_path(request) -> Path:
    """Override default fixture to use `test/yagna/e2e/assets` as default path."""
    import test.yagna.e2e

    path_arg = request.config.option.assets_path
    if path_arg:
        path = Path(path_arg)
    else:
        yagna_e2e_dir_path = Path(test.yagna.e2e.__file__).parent
        path = yagna_e2e_dir_path / "assets"

    if not path.is_dir():
        pytest.fail(
            f"Provided assets path '{path}' doesn't point to an existing directory."
        )

    return path.resolve()


@pytest.fixture
def cancellation_callback() -> Callable[[], None]:
    """Report that the runner was cancelled, do not fail the test.

    This fixture provides the `cancellation_callback` argument to `Runner()`.
    """

    return lambda: logger.info("The runner was cancelled")


@pytest.fixture
def test_failure_callback() -> Callable[[TestFailure], None]:
    """Report the failure, do not fail the test.

    This fixture provides the `test_failure_callback` argument to `Runner()`.
    """

    return lambda error: logger.error(
        f"The runner was stopped due to test failure: {error}"
    )


@pytest.hookimpl
def pytest_report_teststatus(report, config):
    """Suppress printing test status for interactive testing session."""

    # Return section, one-letter and verbose status, e.g. ("failed", "F", "FAILED").
    # Returning empty strings will suppress printing status.
    return "", "", ""  # e.g. "failed", "F", "FAILED"
