#!/usr/bin/env python3
"""Script for downloading artifacts from a GitHub repository."""

import argparse
from pathlib import Path

from goth.runner.download import (
    ArtifactsDownloader,
    DEFAULT_ARTIFACTS,
    DEFAULT_BRANCH,
    DEFAULT_COMMIT,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPO,
    DEFAULT_TOKEN,
    DEFAULT_WORKFLOW,
)

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--branch", default=DEFAULT_BRANCH)
parser.add_argument(
    "-c",
    "--commit",
    default=DEFAULT_COMMIT,
    help="git commit to look for when choosing the workflow run to download from. \
            By default, this value is obtained from env variable YAGNA_COMMIT_HASH. \
            If None, the latest workflow run is used.",
)
parser.add_argument("-o", "--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
parser.add_argument("-r", "--repo", default=DEFAULT_REPO)
parser.add_argument(
    "-t",
    "--token",
    default=DEFAULT_TOKEN,
    help="Access token to be used in GitHub API calls.\
            By default, this value is obtained from env variable GITHUB_API_TOKEN.",
)
parser.add_argument("-w", "--workflow", default=DEFAULT_WORKFLOW)
parser.add_argument(
    "-v", "--verbose", help="If set, enables debug logging.", action="store_true"
)
parser.add_argument(
    "artifacts",
    nargs="*",
    default=DEFAULT_ARTIFACTS,
    help="List of artifact names which should be downloaded. \
            These can be substrings, as well as exact names (with extensions).",
)


if __name__ == "__main__":
    args = parser.parse_args()
    downloader = ArtifactsDownloader(
        repo=args.repo, token=args.token, verbose=args.verbose
    )
    downloader.download(**vars(args))
