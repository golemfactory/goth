#!/usr/bin/env python3
"""Downloader for GitHub repo releases using GitHub's REST API."""

import logging
import os
from pathlib import Path
from typing import Optional

import requests

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)-30s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ENV_API_TOKEN = "GITHUB_API_TOKEN"

DEFAULT_CONTENT_TYPE = "application/vnd.debian.binary-package"
DEFAULT_TOKEN = os.getenv(ENV_API_TOKEN)

BASE_URL = "https://api.github.com/repos"
REPO_OWNER = "golemfactory"

repo_url = ""
session = requests.Session()


def _setup_session(repo: str, token: str):
    global repo_url
    repo_url = BASE_URL + f"/{REPO_OWNER}/{repo}"
    session.headers["Authorization"] = f"token {token}"


def _get_latest_release() -> dict:
    """Get the latest version, this includes pre-releases."""
    url = f"{repo_url}/releases"
    logger.info("fetching releases. url=%s", url)
    response = session.get(url)
    response.raise_for_status()

    releases = response.json()
    logger.debug("releases=%s", releases)

    return releases[0]


def _download(release: dict, content_type: str, output_path: Path):
    """Download an asset from a specific GitHub release."""
    assets = release["assets"]
    logger.debug("assets=%s", assets)
    asset = next(filter(lambda a: a["content_type"] == content_type, assets))
    logger.info("found matching asset. name=%s", asset["name"])
    logger.debug("asset=%s", asset)

    download_url = asset["browser_download_url"]
    with session.get(download_url) as response:
        response.raise_for_status()
        logger.info("downloading asset. url=%s", download_url)
        with output_path.open(mode="wb") as fd:
            fd.write(response.content)
        logger.info("downloaded asset. path=%s", str(output_path))


def download_release(
    repo: str,
    content_type: str = DEFAULT_CONTENT_TYPE,
    output: Optional[Path] = None,
    token: Optional[str] = DEFAULT_TOKEN,
    verbose: bool = False,
):
    """Download the latest release from a given GitHub repo.

    The GitHub user name used in this function is `golemfactory`.

    :param repo: name of the repo to download from
    :param content_type: content-type string for the asset to download
    :param output: file path to where the asset should be downloaded
    :param token: GitHub API token
    :param verbose: enables debug logging when set
    """
    if not token:
        raise ValueError("GitHub token was not provided.")
    if verbose:
        logger.setLevel(logging.DEBUG)

    _setup_session(repo, token)
    output = output or Path(f"./{repo}.deb")

    release = _get_latest_release()
    _download(release, content_type, output)
