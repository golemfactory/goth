"""Module containing logic for running commands in subprocesses."""

import asyncio
import logging
import subprocess
import sys
from typing import Optional, Sequence

from goth.runner.exceptions import CommandError

logger = logging.getLogger(__name__)

RUN_COMMAND_SLEEP_INTERVAL = 0.1  # seconds
RUN_COMMAND_DEFAULT_TIMEOUT = 900  # seconds


class ProcessMonitor:
    """Monitor enabling acquisition of the process object of a running command."""

    _process: Optional[asyncio.subprocess.Process] = None

    async def get_process(self) -> asyncio.subprocess.Process:
        """Wait for and return the `Process` object."""
        while not self._process:
            await asyncio.sleep(0.1)
        return self._process


async def run_command(
    args: Sequence[str],
    env: Optional[dict] = None,
    log_level: Optional[int] = logging.DEBUG,
    cmd_logger: Optional[logging.Logger] = None,
    log_prefix: Optional[str] = None,
    timeout: float = RUN_COMMAND_DEFAULT_TIMEOUT,
    process_monitor: Optional[ProcessMonitor] = None,
) -> None:
    """Run a command in a subprocess with timeout and logging.

    Lines from stdout and stderr of the subprocess are captured and emitted via
    a locally configured `logging` module logger.

    :param args: sequence consisting of the program to run along with its arguments
    :param env: dict with environment for the command
    :param log_level: logging level at which command output will be logged
    :param cmd_logger: optional logger instance used to log output from the command;
        if not set the default module logger will be used
    :param log_prefix: prefix for log lines with command output; ignored if `cmd_logger`
        is specified. Default: name of the command
    :param timeout: timeout for the command, in seconds. Default: 15 minutes
    :param process_monitor: an optional `ProcessMonitor` to which the spawned process
        will be reported, so that it can be communicated with from the calling code
    """
    logger.info("Running local command: %s", " ".join(args))

    if cmd_logger:
        log_prefix = ""
    else:
        cmd_logger = logger
        if log_prefix is None:
            log_prefix = f"[{args[0]}] "

    async def _run_command():
        if sys.platform != "win32":
            proc = await asyncio.subprocess.create_subprocess_exec(
                *args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )

            if process_monitor:
                process_monitor._process = proc

            while not proc.stdout.at_eof():
                line = await proc.stdout.readline()
                cmd_logger.log(log_level, "%s%s", log_prefix, line.decode("utf-8").rstrip())

            return_code = await proc.wait()
            if return_code:
                raise CommandError(
                    f"Command exited abnormally. args={args}, return_code={return_code}"
                )
        else:
            # windows does not support asyncio subprocesses in async pytest
            logger.info(f"Running command (blocking): {args}")
            p = subprocess.Popen(args, env=env)

            while p.poll() is None:
                await asyncio.sleep(1.0)

            out, err = p.communicate()
            if p.returncode != 0:
                raise CommandError(
                    f"Command exited abnormally. args={args}, return_code={p.returncode}"
                )

    await asyncio.wait_for(_run_command(), timeout=timeout)
