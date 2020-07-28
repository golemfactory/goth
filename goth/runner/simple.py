"""A minimal runner implementation."""
import asyncio
import functools
import logging
from pathlib import Path
import time
from typing import List, Optional

from goth.runner import Runner
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.probe import Probe


logger = logging.getLogger(__name__)


def step(default_timeout: float = 10.0):
    """Wrap a step function to implement timeout and log progress."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: Probe, *args, timeout: Optional[float] = None):
            timeout = timeout if timeout is not None else default_timeout
            step_name = f"{self.name}.{func.__name__}(timeout={timeout})"
            start_time = time.time()

            logger.info("Running step '%s'", step_name)
            try:
                result = await asyncio.wait_for(func(self, *args), timeout=timeout)
                self.runner.check_assertion_errors()
                step_time = time.time() - start_time
                logger.debug(
                    "Finished step '%s', result: %s, time: %s",
                    step_name,
                    result,
                    step_time,
                )
            except Exception as exc:
                step_time = time.time() - start_time
                logger.error(
                    "Step '%s' raised %s in %s",
                    step_name,
                    exc.__class__.__name__,
                    step_time,
                )
                raise
            return result

        return wrapper

    return decorator


# TODO: Consider adding `__aenter()__`/`__axit()__` directly to `Runner`
# and removing this class altogether
class SimpleRunner(Runner):
    """A minimal runner implementation.

    Provides the `__aenter__()` method that starts probes and the proxy,
    and the `__aexit()__` method that stops them.
    """

    def __init__(
        self,
        topology: List[YagnaContainerConfig],
        api_assertions_module: Optional[str],
        logs_path: Path,
        assets_path: Optional[Path],
    ):
        super().__init__(topology, api_assertions_module, logs_path, assets_path)

    async def __aenter__(self) -> "SimpleRunner":
        self._start_nodes()
        return self

    # TODO: should we handle args in `__aexit__()` instead of ignoring them?
    async def __aexit__(self, _exc_type, _exc, _traceback):
        await asyncio.sleep(2.0)
        for probe in self.probes:
            self.logger.info("stopping probe. name=%s", probe.name)
            await probe.stop()

        self.proxy.stop()
        # Stopping the proxy triggered evaluation of assertions
        # "at the end of events".
        self.check_assertion_errors()
