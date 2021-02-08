"""Interactive runner for `goth` network."""
import asyncio
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Dict, Optional

from goth.address import (
    YAGNA_BUS_PORT,
    YAGNA_REST_PORT,
)
from goth.configuration import Configuration, load_yaml
from goth.runner import Runner
from goth.runner.container.compose import ComposeConfig, YagnaBuildEnvironment
from goth.runner.log import configure_logging
from goth.runner.probe import RequestorProbe
from goth.runner.provider import ProviderProbeWithLogSteps


logger = logging.getLogger(__name__)


def make_logs_dir(base_dir: Path) -> Path:
    """Create a unique subdirectory for this test run."""

    date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
    log_dir = base_dir / f"goth_{date_str}"
    log_dir.mkdir(parents=True)

    return log_dir


async def start_network(
    configuration: Configuration,
    logs_base_dir: Path = Path("goth-logs"),
    build_env_args: Optional[Dict[str, str]] = None,
    console_log_level: Optional[str] = None,
):
    """Start a test network descsribed by `configuration`."""

    if build_env_args is not None:
        yagna_binary_path = build_env_args.get("yagna-binary-path")
        build_env = YagnaBuildEnvironment(
            docker_dir=configuration.docker_dir,
            release_tag=build_env_args.get("yagna-release"),
            binary_path=Path(yagna_binary_path)
            if yagna_binary_path is not None
            else None,
            branch=None,
            commit_hash=build_env_args.get("yagna-commit-hash"),
            deb_path=None,
        )
    else:
        build_env = None

    # TODO: this should belong to the configuration:
    log_patterns = {
        "ethereum": ".*Wallets supplied.",
        "zksync": ".*Running on http://0.0.0.0:3030/.*",
    }

    compose_config = ComposeConfig(
        build_env=build_env,
        file_path=configuration.compose_file,
        log_patterns=log_patterns,
    )

    def _handle_test_failure(_err):
        # Interrupt the runner on failure
        loop = asyncio.get_event_loop()

        async def _interrupt():
            raise KeyboardInterrupt()

        loop.create_task(_interrupt())

    logs_dir = make_logs_dir(logs_base_dir)
    configure_logging(logs_dir, console_log_level)

    runner = Runner(
        api_assertions_module=None,
        compose_config=compose_config,
        logs_path=logs_dir,
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


if __name__ == "__main__":

    # TODO: find out how to specify the command-line arguments in a modular way,
    # so that arguments for each component (e.g. build environment, web server)
    # are defined and handled in the component's module, rather than having one
    # bulky, monolithic parser definition here.
    import argparse

    build_env_options = {
        "yagna-binary-path": (
            "path to local directory or archive containing yagna binaries"
        ),
        "yagna-commit-hash": (
            "git commit hash in yagna repo for which to download binaries"
        ),
        "yagna-release": (
            "release tag substring specifying which yagna release should be used. "
            "If this is equal to 'latest', latest yagna release will be used."
        ),
    }

    parser = argparse.ArgumentParser("Run GoTH test network")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING"],
        default=logging.INFO,
        help="Log level for the console log",
    )
    parser.add_argument(
        "configuration",
        type=Path,
        help="Network configuration in YAML format",
    )
    # TODO: do we want to add such an option? will this be useful?
    parser.add_argument(
        "--dont-build-images",
        action="store_true",
        help="Do not build docker images for yagna",
    )

    group = parser.add_argument_group(
        title="build-env", description="Build environment options"
    )
    for opt, help in build_env_options.items():
        group.add_argument(f"--{opt}", action="store", help=help)
    args = parser.parse_args()

    configuration = load_yaml(args.configuration)

    if args.dont_build_images:
        build_env_args = None
    else:
        build_env_args = {
            key: vars(args)[key.replace("-", "_")] for key in build_env_options
        }

    loop = asyncio.get_event_loop()
    task = start_network(
        configuration, build_env_args=build_env_args, console_log_level=args.log_level
    )
    loop.run_until_complete(task)
