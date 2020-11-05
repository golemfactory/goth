"""Module containing logic for running commands in subprocesses."""

import asyncio
import logging
import subprocess
from typing import Optional, Sequence

from goth.runner.exceptions import CommandError

logger = logging.getLogger(__name__)

RUN_COMMAND_SLEEP_INTERVAL = 0.1  # seconds
RUN_COMMAND_DEFAULT_TIMEOUT = 900  # seconds


async def run_command(
    args: Sequence[str],
    env: Optional[dict] = None,
    log_prefix: Optional[str] = None,
    timeout: int = RUN_COMMAND_DEFAULT_TIMEOUT,
):
    """Run a command in a subprocess with timeout and logging.

    Lines from stdout and stderr of the subprocess are captured and emitted via
    a locally configured `logging` module logger.

    :param args: sequence consisting of the program to run along with its arguments
    :param env: dict with environment for the command
    :param log_prefix: prefix for log lines emitted. Default: name of the command
    :param timeout: timeout for the command, in seconds. Default: 15 minutes
    """
    logger.info("Running local command: %s", " ".join(args))

    if log_prefix is None:
        log_prefix = f"[{args[0]}] "

    p = subprocess.Popen(
        args=args, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    async def _read_output():
        for line in p.stdout:
            logger.debug("%s%s", log_prefix, line.decode("utf-8").rstrip())

        return_code = p.poll()
        if return_code:
            raise CommandError(
                f"Command exited abnormally. args={args}, return_code={return_code}"
            )
        else:
            await asyncio.sleep(RUN_COMMAND_SLEEP_INTERVAL)

    await asyncio.wait_for(_read_output(), timeout=timeout)
