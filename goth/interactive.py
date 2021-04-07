"""Interactive runner for `goth` network."""
import asyncio
import logging
from pathlib import Path
from typing import Optional

from goth.configuration import Configuration
from goth.runner import Runner
from goth.runner.probe import ProviderProbe, RequestorProbe


logger = logging.getLogger(__name__)


async def start_network(
    configuration: Configuration,
    log_dir: Optional[Path] = None,
):
    """Start a test network described by `configuration`."""

    runner = Runner(
        base_log_dir=log_dir,
        compose_config=configuration.compose_config,
        test_name="interactive",
        api_assertions_module=None,
        web_root_path=configuration.web_root,
        cancellation_callback=lambda: logger.info("The runner was cancelled"),
    )

    async with runner(configuration.containers):

        providers = runner.get_probes(probe_type=ProviderProbe)
        requestor = runner.get_probes(probe_type=RequestorProbe)[0]

        # Some test steps may be included in the interactive test as well
        for provider in providers:
            await provider.wait_for_offer_subscribed(timeout=10)

        print("\n\033[33;1mNow run your requestor agent as follows:\n")
        env = {"PATH": "$PATH"}
        requestor.set_agent_env_vars(env)
        env_vars = " ".join([f"{key}={val}" for key, val in env.items()])
        subnet = providers[0].provider_agent.subnet
        print(f"$ {env_vars} examples/blender/blender.py --subnet {subnet}")

        print("\nPress Ctrl+C at any moment to stop the test harness.\033[0m\n")

        while True:
            await asyncio.sleep(5)
