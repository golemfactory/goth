"""Main entry point to `goth`."""
import argparse
import asyncio
from datetime import datetime, timezone
import logging
from pathlib import Path
import shutil

from goth.configuration import load_yaml
from goth.interactive import start_network
from goth.runner.log import configure_logging, DEFAULT_LOG_DIR


DEFAULT_ASSETS_DIR = Path(__file__).parent / "default-assets"


logger = logging.getLogger(__name__)


def make_logs_dir(base_dir: Path) -> Path:
    """Create a unique subdirectory for this test run."""

    date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
    log_dir = base_dir / f"goth_{date_str}"
    log_dir.mkdir(parents=True)

    return log_dir


def start(args):
    """Start the test network using a configuration read from `args.config_file`."""

    configuration = load_yaml(args.config_file)

    base_log_dir = args.log_dir or DEFAULT_LOG_DIR
    log_dir = make_logs_dir(Path(base_log_dir))
    configure_logging(log_dir, args.log_level)

    loop = asyncio.get_event_loop()
    task = start_network(configuration, log_dir=log_dir)
    loop.run_until_complete(task)


def create_config(args):
    """Create sample asset files in the directory specified by `args.output_dir`.

    Will also create the directory if it does not exist yet.
    If any asset file already exists at the given location, it will be overwritten
    if `args.overwrite` is set, otherwise an exception will be raised.
    """

    output_dir = Path(args.output_dir).resolve()

    input_dir = DEFAULT_ASSETS_DIR

    logger.info("Copying default assets from %s to %s", input_dir, output_dir)
    shutil.copytree(input_dir, output_dir, dirs_exist_ok=args.overwrite)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="goth")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=logging.INFO,
        help="Log level for the console log",
    )

    subparsers = parser.add_subparsers(
        help="a command to run; add --help to see command-specific options"
    )

    parser_start = subparsers.add_parser("start", help="start a test network")
    parser_start.add_argument(
        "config_file",
        metavar="CONFIG-FILE",
        help="configuration file for a test network",
    )
    parser_start.add_argument(
        "--log-dir", type=str, help="Base directory for goth logs for this run"
    )
    parser_start.set_defaults(function=start)

    parser_cfg = subparsers.add_parser(
        "create-assets", help="create a default network configuration and assets"
    )
    parser_cfg.add_argument(
        "output_dir",
        metavar="OUTPUT-DIR",
        help="target directory for test network configuration and assets",
    )
    parser_cfg.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing asset files"
    )
    parser_cfg.set_defaults(function=create_config)

    args = parser.parse_args()
    try:
        args.function(args)
    except AttributeError:
        parser.print_help()
