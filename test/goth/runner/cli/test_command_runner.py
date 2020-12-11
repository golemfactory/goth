"""Tests for `runner.cli.base`.

Containing:
- `runner.cli.base.CommandRunner`
- `runner.cli.base.DockerCommandRunner`
"""
import shlex

import pytest
from unittest.mock import patch

from goth.runner.cli.base import CommandRunner, DockerCommandRunner
from goth.runner.exceptions import CommandError

parameter_names = "command, expected_stdout, expected_stderr"
parameter_values = [
    ("echo STDOUT; echo STDERR >&2", "STDOUT\n", "STDERR\n"),
    ("echo STDOUT", "STDOUT\n", ""),
    ("echo STDERR >&2", "", "STDERR\n"),
]


@pytest.mark.parametrize(parameter_names, parameter_values)
@patch("goth.runner.cli.base.logger")
def test_runner_output_demuxing(_logger, command, expected_stdout, expected_stderr):
    """Test that stdout/stderr from a command are demultiplexed."""

    runner = CommandRunner("/bin/sh")

    stdout, stderr = runner.run_command("-c", command)
    assert stdout == expected_stdout
    assert stderr == expected_stderr


@patch("goth.runner.cli.base.logger")
def test_runner_error_raising(_logger, yagna_container):
    """Test that the correct error is raised when command exits with non-zero code."""

    runner = CommandRunner("/bin/sh")

    with pytest.raises(CommandError) as ce:
        runner.run_command("-c", "echo STDOUT; no-such-command")

    assert "STDOUT" not in str(ce)
    assert "no-such-command" in str(ce)


@pytest.mark.parametrize(parameter_names, parameter_values)
@patch("goth.runner.cli.base.logger")
def test_json_runner_output_demuxing(
    _logger, yagna_container, command, expected_stdout, expected_stderr
):
    """Test that stdout/stderr from a command are demultiplexed."""

    runner = DockerCommandRunner(yagna_container, "/bin/sh")

    stdout, stderr = runner.run_command("-c", shlex.quote(command))
    assert stdout == expected_stdout
    assert stderr == expected_stderr


@patch("goth.runner.cli.base.logger")
def test_json_runner_error_raising(_logger, yagna_container):
    """Test that the correct error is raised when command exits with non-zero code."""

    runner = DockerCommandRunner(yagna_container, "/bin/sh")

    with pytest.raises(CommandError) as ce:
        runner.run_command("-c", "'echo STDOUT; no-such-command'")

    assert "STDOUT" not in str(ce)
    assert "no-such-command" in str(ce)
