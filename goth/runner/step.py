"""A minimal runner implementation."""
import asyncio
import functools
import logging
import time
from typing import Optional, TYPE_CHECKING

from goth.runner.exceptions import StepTimeoutError

if TYPE_CHECKING:
    from goth.runner.probe import Probe

logger = logging.getLogger(__name__)

TIMEOUT_LEFT_WARNING_THRESHOLD = 5


def check_timeout_and_warn(step_name, step_time, timeout)
    if timeout - step_time < TIMEOUT_LEFT_WARNING_THRESHOLD:
        logger.warning(
            "Step '%s' was very close to being timed out: %.1f s."
            "Consider increasing time limit for this step.",
            step_name,
            timeout - step_time,
        )


def step(default_timeout: float = 10.0):
    """Wrap a step function to implement timeout and log progress."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: "Probe", *args, timeout: Optional[float] = None):
            timeout = timeout if timeout is not None else default_timeout
            step_name = f"{self.name}.{func.__name__}(timeout={timeout})"
            start_time = time.time()

            logger.info("Running step '%s'", step_name)
            try:
                result = await asyncio.wait_for(func(self, *args), timeout=timeout)
                self.runner.check_assertion_errors()
                step_time = time.time() - start_time
                logger.debug(
                    "Finished step '%s', result: %s, time: %.1f s",
                    step_name,
                    result,
                    step_time,
                )
            except asyncio.TimeoutError:
                step_time = time.time() - start_time
                logger.error("Step '%s' timed out after %.1f s", step_name, step_time)
                raise StepTimeoutError(step_name, step_time)
            except Exception as exc:
                step_time = time.time() - start_time
                logger.error(
                    "Step '%s' raised %s in %.1f/%.1f s",
                    step_name,
                    exc.__class__.__name__,
                    step_time,
                    timeout,
                )
                check_timeout_and_warn(step_name, step_time, timeout)
                raise
            step_time = time.time() - start_time
            logger.info("Step '%s' finished: %.1f/%.1f s", step_name, step_time, timeout)
            check_timeout_and_warn(step_name, step_time, timeout)
            return result

        return wrapper

    return decorator
