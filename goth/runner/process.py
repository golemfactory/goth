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

            out, err = await proc.communicate()

            logger.info(f"Command finished with return code: {proc.returncode}")
            # Always log output regardless of success/failure
            if out:
                output_text = out.decode("utf-8").strip()
                cmd_logger.log(log_level, f"{log_prefix}{output_text}")

            if proc.returncode:
                error_msg = f"Command failed (exit code {proc.returncode}): {' '.join(args)}"
                if out:
                    error_msg += f"\nOUTPUT: {out.decode('utf-8').strip()}"
                raise CommandError(error_msg)
        else:
            # windows does not support asyncio subprocesses in async pytest
            logger.info(f"Running command (blocking): {args}")
            p = subprocess.Popen(
                args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            while p.poll() is None:
                await asyncio.sleep(1.0)

            out, err = p.communicate()

            # Always log output regardless of success/failure
            if out:
                cmd_logger.log(log_level, f"{log_prefix}{out.strip()}")
            if err:
                cmd_logger.log(log_level, f"{log_prefix}STDERR: {err.strip()}")

            if p.returncode != 0:
                error_msg = f"Command failed (exit code {p.returncode}): {' '.join(args)}"
                if out:
                    error_msg += f"\nSTDOUT: {out.strip()}"
                if err:
                    error_msg += f"\nSTDERR: {err.strip()}"
                raise CommandError(error_msg)

    await asyncio.wait_for(_run_command(), timeout=timeout)
