#!/usr/bin/env python3
"""Script to download artifacts from a github repository."""

import argparse
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Callable, List, Optional

import requests

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)-30s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ENV_API_TOKEN = "GITHUB_API_TOKEN"
ENV_YAGNA_COMMIT = "YAGNA_COMMIT_HASH"

ARTIFACT_NAMES = ["Yagna Linux"]
BRANCH = "master"
REPO_OWNER = "golemfactory"
REPO_NAME = "yagna"
WORKFLOW_NAME = "CI"

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--branch", default=BRANCH)
parser.add_argument(
    "-c",
    "--commit",
    default=os.getenv(ENV_YAGNA_COMMIT),
    help="git commit to look for when choosing the workflow run to download from. \
            By default, the latest workflow run is used. \
            This value can also be specified using the YAGNA_COMMIT_HASH env variable.",
)
parser.add_argument("-o", "--output-dir", default=Path("."))
parser.add_argument("-r", "--repo", default=REPO_NAME)
parser.add_argument(
    "-t",
    "--token",
    default=os.getenv(ENV_API_TOKEN),
    help="Access token to be used in GitHub API calls.\
            By default, this value is obtained from env variable GITHUB_API_TOKEN.",
)
parser.add_argument("-w", "--workflow", default=WORKFLOW_NAME)
parser.add_argument(
    "-v", "--verbose", help="If set, enables debug logging.", action="store_true"
)
parser.add_argument(
    "artifacts",
    nargs="*",
    default=ARTIFACT_NAMES,
    help="List of artifact names which should be downloaded. \
            These can be substrings, as well as exact names (with extensions).",
)
args = parser.parse_args()

if not args.token:
    raise ValueError("GitHub token was not provided.")
if args.verbose:
    logger.setLevel(logging.DEBUG)

BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{args.repo}"
session = requests.Session()
session.headers["Authorization"] = f"token {args.token}"


def _search_with_pagination(
    initial_request: requests.PreparedRequest,
    selector: Callable[[requests.Response], Any],
):
    """Search response data with `Link` header pagination support.

    First request is made using `initial_request`. Consecutive requests are made based
    on the `Link` header until the last page is reached (i.e. no `next` URL is present).
    The `selector` function is called for each response received. If the result from
    `selector` is non-null, this function exits early returning that result.
    """
    response = session.send(initial_request)
    logger.debug("_search_with_pagination. initial_url=%s", response.url)

    while True:
        response.raise_for_status()

        result = selector(response)
        if result:
            logger.debug("_search_with_pagination. result=%s", result)
            return result

        relation_to_url = _parse_link_header(response.headers["Link"])
        logger.debug("_search_with_pagination. relation_to_url=%s", relation_to_url)
        next_url = relation_to_url.get("next")
        if next_url:
            logger.debug("_search_with_pagination. next_url=%s", next_url)
            response = session.get(next_url)
        else:
            return None


def _parse_link_header(header_value: str) -> dict:
    """Parse URLs and their relative positions from a `Link` header value.

    The value of a `Link` header consists of comma-separated tuples, where each tuple
    has a pagination URL and its `rel` attribute. `rel` describes its URL's relation to
    the request the header originates from. The value of the `rel` attribute is one of
    the following: `first`, `prev`, `next`, `last`.
    """
    relation_to_url = {}
    links = [link.strip() for link in header_value.split(",")]

    for link in links:
        result = re.search(r'<(\S+)>; rel="(\S+)"', link)
        if not result:
            raise LookupError

        url = result.group(1)
        relation = result.group(2)
        relation_to_url[relation] = url

    return relation_to_url


def get_workflow(workflow_name: str) -> dict:
    """Query the workflow on github."""
    url = f"{BASE_URL}/actions/workflows"
    logger.info("fetching workflows. url=%s", url)
    response = session.get(url)
    response.raise_for_status()

    workflows = response.json()["workflows"]
    logger.debug("workflows=%s", workflows)
    workflow = next(filter(lambda w: w["name"] == workflow_name, workflows))
    logger.debug("workflow=%s", workflow)
    return workflow


def get_latest_run(workflow_id: str, branch: str, commit: Optional[str] = None) -> dict:
    """Filter out the latest workflow run."""
    url = f"{BASE_URL}/actions/workflows/{workflow_id}/runs"
    params = {"branch": branch, "status": "completed"}
    request = session.prepare_request(requests.Request("GET", url, params=params))
    logger.info("fetching workflow runs. url=%s", request.url)

    def _filter_workflows(response: requests.Response) -> Optional[dict]:
        workflow_runs = response.json()["workflow_runs"]
        if commit:
            return next(
                filter(lambda r: r["head_sha"].startswith(commit), workflow_runs), None
            )
        else:
            return workflow_runs[0]

    workflow_run = _search_with_pagination(request, _filter_workflows)
    logger.debug("workflow_run=%s", workflow_run)
    return workflow_run


def download_artifacts(
    artifacts_url: str, artifact_names: List[str], output_dir: os.PathLike
):
    """Download an artifact from a specific github workflow."""
    logger.info("fetching artifacts. url=%s", artifacts_url)
    response = session.get(artifacts_url)
    response.raise_for_status()

    artifacts = response.json()["artifacts"]
    logger.debug("artifacts=%s", artifacts)
    for name in artifact_names:
        artifact = next(filter(lambda a: name in a["name"], artifacts), None)
        if not artifact:
            logger.warning("failed to find artifact. artifact_name=%s", name)
            continue

        logger.info("found matching artifact. artifact=%s", artifact)
        archive_url = artifact["archive_download_url"]
        with session.get(archive_url) as response:
            response.raise_for_status()
            logger.info("downloading artifact. url=%s", archive_url)
            with tempfile.NamedTemporaryFile() as fd:
                fd.write(response.content)
                logger.debug("extracting zip archive. path=%s", fd.name)
                shutil.unpack_archive(
                    fd.name, format="zip", extract_dir=str(output_dir)
                )
        logger.info("extracted package. path=%s", output_dir)


if __name__ == "__main__":
    logger.info(
        "workflow=%s, artifacts=%s, commit=%s",
        args.workflow,
        args.artifacts,
        args.commit,
    )

    workflow = get_workflow(args.workflow)
    last_run = get_latest_run(workflow["id"], args.branch, args.commit)
    download_artifacts(last_run["artifacts_url"], args.artifacts, args.output_dir)
