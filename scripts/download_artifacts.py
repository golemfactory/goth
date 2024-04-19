#!/usr/bin/env python3
"""Script for downloading artifacts from a GitHub Actions workflow run."""

import argparse
from pathlib import Path

from goth.runner.download import (
    ArtifactDownloader,
    DEFAULT_ARTIFACT,
    DEFAULT_BRANCH,
    DEFAULT_COMMIT,
    DEFAULT_REPO,
    DEFAULT_TOKEN,
    DEFAULT_WORKFLOW,
)

parser = argparse.ArgumentParser()
parser.add_argument(
    "-a",
    "--artifact",
    default=DEFAULT_ARTIFACT,
    help="Name of the artifact to be downloaded. \
            This can be a substring, as well as an exact name (with extension).",
)
parser.add_argument(
    "-b",
    "--branch",
    default=DEFAULT_BRANCH,
    help="git branch to use when selecting the workflow run.",
)
parser.add_argument(
    "-c",
    "--commit",
    default=DEFAULT_COMMIT,
    help="git commit to look for when choosing the workflow run to download from. \
            By default, this value is obtained from env variable YAGNA_COMMIT_HASH. \
            If None, the latest workflow run is used.",
)
parser.add_argument(
    "-o",
    "--output",
    type=Path,
    help="Output directory to which the extracted artifacts should be saved.",
)
parser.add_argument("-r", "--repo", default=DEFAULT_REPO)
parser.add_argument(
    "-t",
    "--token",
    default=DEFAULT_TOKEN,
    help="Access token to be used in GitHub API calls.\
            By default, this value is obtained from env variable GITHUB_TOKEN.",
)
parser.add_argument("-w", "--workflow", default=DEFAULT_WORKFLOW)
parser.add_argument("-v", "--verbose", help="If set, enables debug logging.", action="store_true")


if __name__ == "__main__":
    args = parser.parse_args()
    downloader = ArtifactDownloader(repo=args.repo, token=args.token, verbose=args.verbose)
    downloader.download(args.artifact, args.branch, args.commit, args.output, args.workflow)
