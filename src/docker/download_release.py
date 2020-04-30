#!/usr/bin/env python3

import argparse
import logging
import os
from pathlib import Path

import requests

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)-30s %(message)s", level=logging.INFO,
)
logger = logging.getLogger(__name__)

ENV_API_TOKEN = "GITHUB_API_TOKEN"

CONTENT_TYPE = "application/vnd.debian.binary-package"
REPO_OWNER = "golemfactory"
REPO_NAME = "ya-runtime-wasi"

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--content-type", default=CONTENT_TYPE)
parser.add_argument("-o", "--output", default="release.deb")
parser.add_argument("-r", "--repo", default=REPO_NAME)
parser.add_argument("-t", "--token", default=os.environ[ENV_API_TOKEN])
args = parser.parse_args()

BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{args.repo}"
session = requests.Session()
session.headers["Authorization"] = f"token {args.token}"


def get_latest_release() -> dict:
    """ Includes pre-releases """
    url = f"{BASE_URL}/releases"
    logger.info("fetching releases. url=%s", url)
    response = session.get(url)
    response.raise_for_status()

    releases = response.json()
    logger.debug("releases=%s", releases)
    latest = releases[0]
    logger.info("got latest release. release=%s", latest)

    return latest


def download_asset(release: dict, content_type: str, output_path: str):
    assets = release["assets"]
    logger.debug("assets=%s", assets)
    asset = next(filter(lambda a: a["content_type"] == content_type, assets))
    logger.info("found matching asset. asset=%s", asset)

    download_url = asset["browser_download_url"]
    with session.get(download_url) as response:
        response.raise_for_status()
        logger.info("downloading asset. url=%s", download_url)
        with Path(output_path).open(mode="wb") as fd:
            fd.write(response.content)
        logger.info("downloaded asset. path=%s", output_path)


if __name__ == "__main__":
    release = get_latest_release()
    download_asset(release, args.content_type, args.output)
