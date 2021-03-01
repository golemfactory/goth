"""Interactive runner for `goth` network."""
import asyncio
import logging
from pathlib import Path

from goth.address import (
    YAGNA_BUS_PORT,
    YAGNA_REST_PORT,
)
from goth.configuration import Configuration
from goth.runner import Runner
from goth.runner.probe import RequestorProbe
from goth.runner.provider import ProviderProbeWithLogSteps


logger = logging.getLogger(__name__)


async def start_network(
    configuration: Configuration,
    log_dir: Path = Path("goth-logs"),
):
    """Start a test network described by `configuration`."""

    def _handle_test_failure(_err):
        # Interrupt the runner on failure
        loop = asyncio.get_event_loop()

        async def _interrupt():
            raise KeyboardInterrupt()

        loop.create_task(_interrupt())

    runner = Runner(
        api_assertions_module=None,
        compose_config=configuration.compose_config,
        log_dir=log_dir,
        web_root_path=configuration.web_root,
        cancellation_callback=lambda: logger.info("The runner was cancelled"),
        test_failure_callback=_handle_test_failure,
    )

    async with runner(configuration.containers):

        providers = runner.get_probes(probe_type=ProviderProbeWithLogSteps)
        requestor = runner.get_probes(probe_type=RequestorProbe)[0]

        # Some test steps may be included in the interactive test as well
        for provider in providers:
            await provider.wait_for_offer_subscribed(timeout=10)

        print("\n\033[33;1mNow run your requestor agent as follows:\n")
        print(
            f"$  YAGNA_APPKEY={requestor.app_key} "
            f"YAGNA_API_URL=http://{requestor.ip_address}:{YAGNA_REST_PORT} "
            f"GSB_URL=tcp://{requestor.ip_address}:{YAGNA_BUS_PORT} "
            f"examples/blender/blender.py --subnet {providers[0].subnet}"
        )

        print("\nPress Ctrl+C at any moment to stop the test harness.\033[0m\n")

        while True:
            await asyncio.sleep(5)
