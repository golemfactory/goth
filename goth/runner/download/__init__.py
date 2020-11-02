"""Package related to downloading assets necessary for building yagna images."""

from abc import ABC
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Callable, Optional

import requests

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)-35s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ASSET_CACHE_DIR = Path(tempfile.gettempdir()) / "goth_asset_cache"

BASE_URL = "https://api.github.com/repos"

ENV_API_TOKEN = "GITHUB_API_TOKEN"
ENV_YAGNA_COMMIT = "YAGNA_COMMIT_HASH"

DEFAULT_ARTIFACT = "Yagna Linux"
DEFAULT_BRANCH = "master"
DEFAULT_COMMIT = os.getenv(ENV_YAGNA_COMMIT)
DEFAULT_CONTENT_TYPE = "application/vnd.debian.binary-package"
DEFAULT_OWNER = "golemfactory"
DEFAULT_REPO = "yagna"
DEFAULT_TOKEN = os.getenv(ENV_API_TOKEN)
DEFAULT_WORKFLOW = "CI"


class GithubDownloader(ABC):
    """Base class for downloading assets using GitHub's REST API."""

    repo_url: str
    """Repo URL to be used as base in API requests."""
    session: requests.Session
    """Session object for making HTTP requests."""

    def __init__(
        self,
        owner: str = DEFAULT_OWNER,
        purge_cache: bool = False,
        repo: str = DEFAULT_REPO,
        token: Optional[str] = DEFAULT_TOKEN,
        verbose: bool = False,
    ):
        if not token:
            raise ValueError("GitHub token was not provided.")

        if verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        if purge_cache:
            shutil.rmtree(ASSET_CACHE_DIR)

        self.repo_url = BASE_URL + f"/{owner}/{repo}"
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"token {token}"

    def _cache_get(self, asset_id: str) -> Optional[Path]:
        asset_path: Path = ASSET_CACHE_DIR / asset_id

        if asset_path.is_dir() and list(asset_path.glob("*")):
            return asset_path

        return None

    def _create_cache_dir(self, asset_id: str) -> Path:
        asset_path: Path = ASSET_CACHE_DIR / asset_id
        asset_path.mkdir(exist_ok=True, parents=True)
        return asset_path

    def _parse_link_header(self, header_value: str) -> dict:
        """Parse URLs and their relative positions from a `Link` header value.

        The value of a `Link` header consists of comma-separated tuples, where each
        tuple has a pagination URL and its `rel` attribute.
        `rel` describes its URL's relation to the request the header originates from.
        The value of the `rel` attribute is one of the following:
        `first`, `prev`, `next`, `last`.
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

    def _search_with_pagination(
        self,
        initial_request: requests.PreparedRequest,
        selector: Callable[[requests.Response], Any],
    ):
        """Search response data with `Link` header pagination support.

        First request is made using `initial_request`. Consecutive requests are made
        based on the `Link` header until the last page is reached
        (i.e. no `next` URL is present). The `selector` function is called for each
        response received. If the result from `selector` is non-null, this function
        exits early returning that result.
        """
        response = self.session.send(initial_request)
        logger.debug("_search_with_pagination. initial_url=%s", response.url)

        while True:
            response.raise_for_status()

            result = selector(response)
            if result:
                logger.debug("_search_with_pagination. result=%s", result)
                return result

            relation_to_url = self._parse_link_header(response.headers["Link"])
            logger.debug("_search_with_pagination. relation_to_url=%s", relation_to_url)
            next_url = relation_to_url.get("next")
            if next_url:
                logger.debug("_search_with_pagination. next_url=%s", next_url)
                response = self.session.get(next_url)
            else:
                return None


class ArtifactDownloader(GithubDownloader):
    """Downloader for GitHub Actions artifacts using GitHub's REST API."""

    def _get_workflow(self, workflow_name: str) -> dict:
        """Query the workflow on GitHub Actions."""
        url = f"{self.repo_url}/actions/workflows"
        logger.info("fetching workflows. url=%s", url)
        response = self.session.get(url)
        response.raise_for_status()

        workflows = response.json()["workflows"]
        logger.debug("workflows=%s", workflows)
        workflow = next(filter(lambda w: w["name"] == workflow_name, workflows))
        logger.debug("workflow=%s", workflow)
        return workflow

    def _get_latest_run(
        self, workflow: dict, branch: str, commit: Optional[str] = None
    ) -> dict:
        """Filter out the latest workflow run."""
        workflow_id = workflow["id"]
        url = f"{self.repo_url}/actions/workflows/{workflow_id}/runs"
        params = {"status": "completed"}
        if not commit:
            params["branch"] = branch

        request = self.session.prepare_request(
            requests.Request("GET", url, params=params)
        )
        logger.info("fetching workflow runs. url=%s", request.url)

        def _filter_workflows(response: requests.Response) -> Optional[dict]:
            workflow_runs = response.json()["workflow_runs"]
            if commit:
                return next(
                    filter(lambda r: r["head_sha"].startswith(commit), workflow_runs),
                    None,
                )
            else:
                return workflow_runs[0]

        workflow_run = self._search_with_pagination(request, _filter_workflows)
        logger.debug("workflow_run=%s", workflow_run)
        return workflow_run

    def _get_artifact(self, artifact_name: str, workflow_run: dict) -> Optional[dict]:
        artifacts_url = workflow_run["artifacts_url"]
        logger.info("fetching artifacts. url=%s", artifacts_url)
        response = self.session.get(artifacts_url)
        response.raise_for_status()

        artifacts = response.json()["artifacts"]
        logger.debug("artifacts=%s", artifacts)
        artifact = next(filter(lambda a: artifact_name in a["name"], artifacts), None)

        return artifact

    def _download_artifact(self, artifact: dict) -> Path:
        """Download an artifact from a specific GitHub Actions workflow run.

        Return path to the extracted artifact.
        """
        artifact_id = str(artifact["id"])
        archive_url = artifact["archive_download_url"]

        with self.session.get(archive_url) as response:
            response.raise_for_status()
            logger.info("downloading artifact. url=%s", archive_url)

            with tempfile.NamedTemporaryFile() as fd:
                fd.write(response.content)
                logger.debug("extracting zip archive. path=%s", fd.name)
                cache_dir = self._create_cache_dir(artifact_id)
                shutil.unpack_archive(fd.name, format="zip", extract_dir=str(cache_dir))
                logger.info("extracted package. path=%s", cache_dir)

        return cache_dir

    def download(
        self,
        artifact_name: str = DEFAULT_ARTIFACT,
        branch: str = DEFAULT_BRANCH,
        commit: Optional[str] = DEFAULT_COMMIT,
        output: Optional[Path] = None,
        workflow_name: str = DEFAULT_WORKFLOW,
    ) -> Optional[Path]:
        """Download an artifact being the result of a given GitHub Actions workflow.

        After downloading, the artifact is extracted and, if specified, saved under
        the directory or file given as `output`.
        Return the download path or `None` if the artifact was not found.

        :param artifact_name: name of the artifact which should be downloaded
        :param branch: git branch to use when selecting the workflow run
        :param commit: git commit to use when selecting the workflow run
        :param output: directory to which the artifact should be extracted
        :param workflow_name: name of the workflow to select a run from
        """
        logger.info(
            "downloading artifact. name=%s, branch=%s, commit=%s, workflow=%s",
            artifact_name,
            branch,
            commit,
            workflow_name,
        )

        workflow = self._get_workflow(workflow_name)
        latest_run = self._get_latest_run(workflow, branch, commit)
        artifact = self._get_artifact(artifact_name, latest_run)
        if not artifact:
            logger.warning("failed to find artifact. name=%s", artifact_name)
            return None
        logger.info("found matching artifact. artifact=%s", artifact)

        artifact_id = str(artifact["id"])
        cache_path = self._cache_get(artifact_id)
        if cache_path:
            logger.info("using cached artifact. cache_path=%s", cache_path)
        else:
            cache_path = self._download_artifact(artifact)

        if output:
            shutil.copytree(cache_path, output, dirs_exist_ok=True)
            logger.info("copied artifact to output path. output=%s", str(output))

        return output or cache_path


class ReleaseDownloader(GithubDownloader):
    """Downloader for GitHub repo releases using GitHub's REST API."""

    repo_name: str
    """Name of the repo to download the release from."""

    def __init__(self, repo: str, *args, **kwargs):
        # mypy error here is a bug: https://github.com/python/mypy/issues/6799
        super().__init__(*args, repo=repo, **kwargs)
        self.repo_name = repo

    def _get_latest_release(self) -> Optional[dict]:
        """Get the latest version, this includes pre-releases."""
        url = f"{self.repo_url}/releases"
        logger.info("fetching releases. url=%s", url)
        response = self.session.get(url)
        response.raise_for_status()

        releases = response.json()
        logger.debug("releases=%s", releases)

        return releases[0] if releases else None

    def _get_asset(self, release: dict, content_type: str) -> Optional[dict]:
        assets = release["assets"]
        logger.debug("assets=%s", assets)
        asset = next(filter(lambda a: a["content_type"] == content_type, assets), None)
        return asset

    def _download_asset(self, asset: dict) -> Path:
        """Download an asset from a specific GitHub release."""
        download_url = asset["browser_download_url"]
        asset_id = str(asset["id"])

        with self.session.get(download_url) as response:
            response.raise_for_status()
            logger.info("downloading asset. url=%s", download_url)
            cache_file = self._create_cache_dir(asset_id) / asset["name"]
            with cache_file.open(mode="wb") as fd:
                fd.write(response.content)
            logger.info("downloaded asset. path=%s", str(cache_file))

        return cache_file

    def download(
        self,
        content_type: str = DEFAULT_CONTENT_TYPE,
        output: Optional[Path] = None,
    ) -> Optional[Path]:
        """Download the latest release (or pre-release) from a given GitHub repo.

        Return the download path or `None` if the asset was not found.
        :param content_type: content-type string for the asset to download
        :param output: file path to where the asset should be saved
        """
        release = self._get_latest_release()
        if not release:
            logger.warning("given repo has no releases. repo=%s", self.repo_name)
            return None

        asset = self._get_asset(release, content_type)
        if not asset:
            logger.warning(
                "failed to find asset of given type. content_type=%s", content_type
            )
            return None
        logger.info("found matching asset. name=%s", asset["name"])
        logger.debug("asset=%s", asset)

        asset_id = str(asset["id"])
        cache_path = self._cache_get(asset_id)
        if cache_path:
            cache_path = cache_path / asset["name"]
            logger.info("using cached release asset. cache_path=%s", cache_path)
        else:
            cache_path = self._download_asset(asset)

        if output:
            shutil.copy2(cache_path, output)
            logger.info("copied release to output path. output=%s", str(output))

        return output or cache_path
