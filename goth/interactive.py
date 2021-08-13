"""Interactive runner for `goth` network."""
import asyncio
import logging
from pathlib import Path
import tempfile
from typing import Dict, Optional

from goth.configuration import Configuration
from goth.runner import Runner
from goth.runner.probe import ProviderProbe, RequestorProbe


logger = logging.getLogger(__name__)

env_file: Path = Path(tempfile.gettempdir()) / "goth_interactive.env"


def _write_env_file(env: Dict[str, str]) -> None:
    with env_file.open("w") as f:
        for key, val in env.items():
            f.write(f"export {key}={val}\n")


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
            await provider.provider_agent.wait_for_log("Subscribed offer")

        requestor_env = requestor.get_agent_env_vars(expand_path=False)
        subnet = providers[0].provider_agent.subnet
        requestor_env["YAGNA_SUBNET"] = subnet

        _write_env_file(requestor_env)
        env_vars = " ".join([f"{key}={val}" for key, val in requestor_env.items()])

        print("\n\033[33;1mLocal goth network ready!")
        print("You can now load the requestor configuration variables to your shell:\n")
        print(f"source {str(env_file)}\n")
        print("And then run your requestor agent from that same shell.")
        print("You can also use the variables directly like so:\n")
        print(f"{env_vars} your/requestor/agent\n")
        print("Press Ctrl+C at any moment to stop the local network.\033[0m\n")

        while True:
            await asyncio.sleep(5)
