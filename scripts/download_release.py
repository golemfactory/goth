#!/usr/bin/env python3
"""Script for downloading releases from a GitHub repository."""

import argparse
from pathlib import Path

from goth.runner.download import (
    ReleaseDownloader,
    DEFAULT_CONTENT_TYPE,
    DEFAULT_TOKEN,
)

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--content-type", default=DEFAULT_CONTENT_TYPE)
parser.add_argument(
    "-o",
    "--output",
    help="Output path, may be either a file or a directory.",
    type=Path,
)
parser.add_argument("-t", "--token", default=DEFAULT_TOKEN)
parser.add_argument(
    "-v", "--verbose", help="If set, enables debug logging.", action="store_true"
)
parser.add_argument(
    "-T",
    "--tag",
    default="",
    help="Tag name substring; only releases with matching tags will be downloaded",
)
parser.add_argument("repo", help="Name of the git repository to be used.")


if __name__ == "__main__":
    args = parser.parse_args()
    downloader = ReleaseDownloader(
        args.repo, token=args.token, verbose=args.verbose, tag_substring=args.tag
    )
    downloader.download(args.content_type, args.output)
