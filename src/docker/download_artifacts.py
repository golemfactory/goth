#!/usr/bin/env python3

import argparse
import logging
import os
import shutil
import tempfile
import typing

import requests

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)-35s %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ENV_API_TOKEN = "GITHUB_API_TOKEN"

ARTIFACT_NAMES = ["yagna_with_router.deb"]
BRANCH = "master"
REPO_OWNER = "golemfactory"
REPO_NAME = "yagna"
WORKFLOW_NAME = "Build .deb"

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--branch", default=BRANCH)
parser.add_argument("-t", "--token", default=os.environ[ENV_API_TOKEN])
parser.add_argument("-w", "--workflow", default=WORKFLOW_NAME)
parser.add_argument("artifacts", nargs="*", default=ARTIFACT_NAMES)
args = parser.parse_args()

BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
session = requests.Session()
session.headers["Authorization"] = f"token {args.token}"


def get_workflow(workflow_name: str) -> dict:
    url = f"{BASE_URL}/actions/workflows"
    logger.info("fetching workflows. url=%s", url)
    response = session.get(f"{BASE_URL}/actions/workflows")
    response.raise_for_status()

    workflows = response.json()["workflows"]
    logger.debug("workflows=%s", workflows)
    result = next(filter(lambda w: w["name"] == workflow_name, workflows))
    logger.debug("result=%s", result)
    return result


def get_latest_run(workflow_id: str) -> dict:
    url = f"{BASE_URL}/actions/workflows/{workflow_id}/runs"
    logger.info("fetching worflow runs. url=%s", url)
    response = session.get(url)
    response.raise_for_status()

    workflow_runs = response.json()["workflow_runs"]
    logger.debug("workflow_runs=%s", workflow_runs)
    result = next(
        filter(
            lambda r: r["conclusion"] == "success"
            and r["head_branch"] == BRANCH,
            workflow_runs,
        )
    )
    logger.debug("result=%s", result)
    return result


def download_artifacts(artifacts_url: str, artifact_names: typing.List[str]):
    logger.info("fetching artifacts. url=%s", artifacts_url)
    response = session.get(artifacts_url)
    response.raise_for_status()

    artifacts = response.json()["artifacts"]
    logger.debug("artifacts=%s", artifacts)
    for name in artifact_names:
        artifact = next(filter(lambda a: a["name"] == name, artifacts), None)
        if not artifact:
            logger.warning("failed to find artifact. artifact_name=%s", name)
            continue

        logger.info("found matching artifact. artifact=%s", artifact)
        archive_url = artifact["archive_download_url"]
        with session.get(archive_url, stream=True) as response:
            response.raise_for_status()
            logger.info("downloading artifact. url=%s", archive_url)
            with tempfile.NamedTemporaryFile() as fd:
                shutil.copyfileobj(response.raw, fd)
                logger.debug("extracting zip archive. path=%s", fd.name)
                shutil.unpack_archive(fd.name, format="zip")
        logger.info("extracted package. path=%s", name)


if __name__ == "__main__":
    logger.info("workflow=%s, artifacts=%s", args.workflow, args.artifacts)

    workflow = get_workflow(args.workflow)
    last_run = get_latest_run(workflow["id"])
    download_artifacts(last_run["artifacts_url"], args.artifacts)
