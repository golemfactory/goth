"""Tests for `runner.cli.base.DockerCommandRunner`
and `runner.cli.base.DockerJSONCommandRunner`
"""
import shlex

import pytest

from goth.runner.cli import DockerJSONCommandRunner
from goth.runner.exceptions import CommandError


@pytest.mark.parametrize(
    "command, expected_stdout, expected_stderr",
    [
        ("echo STDOUT; echo STDERR >&2", "STDOUT\n", "STDERR\n"),
        ("echo STDOUT", "STDOUT\n", ""),
        ("echo STDERR >&2", "", "STDERR\n"),
    ],
)
def test_output_demultiplexing(
    yagna_container, command, expected_stdout, expected_stderr
):
    """Test that stdout/stderr from a command are demultiplexed."""

    runner = DockerJSONCommandRunner(yagna_container, "/bin/sh")

    stdout, stderr = runner.run_command("-c", shlex.quote(command))
    assert stdout == expected_stdout
    assert stderr == expected_stderr


def test_error_output_demultiplexing(yagna_container):
    """Test that stdout/stderr from a command are demultiplexed."""

    runner = DockerJSONCommandRunner(yagna_container, "/bin/sh")

    with pytest.raises(CommandError) as ce:
        runner.run_command("-c", "'echo STDOUT; no-such-command'")

    assert "STDOUT" not in str(ce)
    assert "no-such-command" in str(ce)
