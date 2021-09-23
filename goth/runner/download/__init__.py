"""Package related to downloading assets necessary for building yagna images."""

from abc import ABC
import logging
import os
import json
from pathlib import Path
import shutil
import tempfile
from typing import Optional

from ghapi.all import GhApi, paged
from fastcore.utils import obj2dict
import requests

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)-35s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ASSET_CACHE_DIR = Path(tempfile.gettempdir()) / "goth_asset_cache"

ENV_API_TOKEN = "GITHUB_API_TOKEN"
ENV_YAGNA_BRANCH = "YAGNA_BRANCH"
ENV_YAGNA_COMMIT = "YAGNA_COMMIT_HASH"

DEFAULT_ARTIFACT = "Yagna Linux"
DEFAULT_BRANCH = "master"
DEFAULT_COMMIT = os.getenv(ENV_YAGNA_COMMIT)
DEFAULT_CONTENT_TYPE = "application/vnd.debian.binary-package"
DEFAULT_OWNER = "golemfactory"
DEFAULT_REPO = "yagna"
DEFAULT_TOKEN = os.getenv(ENV_API_TOKEN)
DEFAULT_WORKFLOW = "Build binaries (x86-64)"


class AssetNotFound(Exception):
    """Exception raised when a requested asset could not be found."""


class GithubDownloader(ABC):
    """Base class for downloading assets using GitHub's REST API."""

    gh_api: GhApi
    """GitHub REST API client."""

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

        self.gh_api = GhApi(owner=owner, repo=repo, token=token)
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


class ArtifactDownloader(GithubDownloader):
    """Downloader for GitHub Actions artifacts using GitHub's REST API."""

    def _get_workflow(self, workflow_name: str) -> dict:
        """Query the workflow on GitHub Actions."""
        logger.debug("Fetching workflows. name=%s", workflow_name)
        workflows = self.gh_api.actions.list_repo_workflows().workflows
        workflow = next(filter(lambda w: w["name"] == workflow_name, workflows))
        logger.debug("workflow=%s", json.dumps(obj2dict(workflow)))

        return workflow

    def _get_latest_run(
        self, workflow: dict, branch: str, commit: Optional[str] = None
    ) -> Optional[dict]:
        """Filter out the latest successful workflow run."""
        workflow_id = workflow["id"]
        logger.debug("Fetching workflow runs. workflow_id=%s", workflow_id)

        branch_query = lambda run: run["head_branch"] == branch  # noqa: E731
        commit_query = lambda run: run["head_sha"].startswith(commit)  # noqa: E731

        paged_workflow_runs = paged(
            self.gh_api.actions.list_workflow_runs,
            workflow_id,
            conclusion="success",
        )

        for page in paged_workflow_runs:
            latest_run = next(
                filter(commit_query if commit else branch_query, page.workflow_runs),
                None,
            )

            if latest_run:
                logger.debug("latest_run=%s", json.dumps(obj2dict(latest_run)))
                return latest_run
            else:
                logger.debug(
                    "page.workflow_runs=%s", json.dumps(obj2dict(page.workflow_runs))
                )

        return None

    def _get_artifact(self, artifact_name: str, workflow_run: dict) -> Optional[dict]:
        artifacts_url = workflow_run["artifacts_url"]
        logger.debug("Fetching artifacts. url=%s", artifacts_url)
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
        archive_url = artifact["archive_download_url"]

        logger.info("Downloading artifact. url=%s", archive_url)
        with self.session.get(archive_url) as response:
            response.raise_for_status()

        with tempfile.NamedTemporaryFile() as fd:
            fd.write(response.content)
            logger.debug("Extracting zip archive. path=%s", fd.name)
            cache_dir = self._create_cache_dir(str(artifact["id"]))
            shutil.unpack_archive(fd.name, format="zip", extract_dir=str(cache_dir))
            logger.debug("Extracted package. path=%s", cache_dir)
            logger.info("Downloaded artifact. url=%s", archive_url)

        return cache_dir

    def download(
        self,
        artifact_name: str = DEFAULT_ARTIFACT,
        branch: str = DEFAULT_BRANCH,
        commit: Optional[str] = DEFAULT_COMMIT,
        output: Optional[Path] = None,
        workflow_name: str = DEFAULT_WORKFLOW,
    ) -> Path:
        """Download an artifact being the result of a given GitHub Actions workflow.

        After downloading, the artifact is extracted and, if specified, saved under
        the directory or file given as `output`.
        Raise `AssetNotFound` if the requested artifact could not be found.
        Return path containing the downloaded artifact.

        :param artifact_name: name of the artifact which should be downloaded
        :param branch: git branch to use when selecting the workflow run
        :param commit: git commit to use when selecting the workflow run
        :param output: directory to which the artifact should be extracted
        :param workflow_name: name of the workflow to select a run from
        """
        logger.debug(
            "ArtifactDownloader#download. name=%s, branch=%s, commit=%s, workflow=%s",
            artifact_name,
            branch,
            commit,
            workflow_name,
        )
        workflow = self._get_workflow(workflow_name)
        latest_run = self._get_latest_run(workflow, branch, commit)
        if not latest_run:
            raise RuntimeError(
                f"Failed to find latest workflow run. workflow_name={workflow_name}"
            )
        artifact = self._get_artifact(artifact_name, latest_run)
        if not artifact:
            raise AssetNotFound(f"Artifact not found. name={artifact_name}")

        logger.debug("Found matching artifact. artifact=%s", artifact)
        artifact_id = str(artifact["id"])
        cache_path = self._cache_get(artifact_id)
        if cache_path:
            logger.info("Using cached artifact. cache_path=%s", cache_path)
        else:
            cache_path = self._download_artifact(artifact)

        if output:
            shutil.copytree(cache_path, output, dirs_exist_ok=True)
            logger.debug("Copied artifact to output path. output=%s", str(output))

        return output or cache_path


class ReleaseDownloader(GithubDownloader):
    """Downloader for GitHub repo releases using GitHub's REST API."""

    repo_name: str
    """Name of the repo to download the release from."""

    def __init__(self, repo: str, *args, **kwargs):
        # mypy error here is a bug: https://github.com/python/mypy/issues/6799
        super().__init__(*args, repo=repo, **kwargs)
        self.repo_name = repo

    def _get_latest_release(
        self,
        tag_substring: str,
        content_type: str,
        use_unstable: bool = True,
    ) -> Optional[dict]:
        """Get the latest version, this includes pre-releases.

        Only the versions with `tag_name` that contains `self.tag_substring`
        as a substring are considered.
        """
        all_releases = self.gh_api.repos.list_releases()
        logger.debug("releases=%s", json.dumps(obj2dict(all_releases)))

        def release_filter(release: dict, tag_substring: str) -> bool:
            if not use_unstable and release["prerelease"]:
                return False

            has_matching_asset = any(
                asset["content_type"] == content_type for asset in release["assets"]
            )
            has_matching_tag = tag_substring in release["tag_name"]
            return has_matching_asset and has_matching_tag

        matching_releases = (
            rel for rel in all_releases if release_filter(rel, tag_substring)
        )
        return next(matching_releases, None)

    def _get_asset(
        self, release: dict, content_type: str, asset_name: Optional[str] = None
    ) -> Optional[dict]:
        assets = release["assets"]
        logger.debug("assets=%s", json.dumps(obj2dict(assets)))

        content_assets = filter(lambda a: a["content_type"] == content_type, assets)
        if content_assets and asset_name:
            return next(filter(lambda a: asset_name in a["name"], content_assets), None)
        return next(content_assets, None)

    def _download_asset(self, asset: dict) -> Path:
        """Download an asset from a specific GitHub release."""
        download_url = asset["browser_download_url"]

        logger.info("Downloading asset. url=%s", download_url)
        with self.session.get(download_url) as response:
            response.raise_for_status()
            cache_file = self._create_cache_dir(str(asset["id"])) / asset["name"]
            with cache_file.open(mode="wb") as fd:
                fd.write(response.content)
            logger.info("Downloaded asset. path=%s", str(cache_file))

        return cache_file

    def download(
        self,
        asset_name: str = "",
        content_type: str = DEFAULT_CONTENT_TYPE,
        output: Optional[Path] = None,
        tag_substring: str = "",
        use_unstable: bool = True,
    ) -> Path:
        """Download the latest release (or pre-release) from a given GitHub repo.

        Raise `AssetNotFound` if the requested release could not be found or if the
        repo has no releases.
        Return path containing the downloaded release.
        :param asset_name: substring the asset's name must contain
        :param content_type: content-type string for the asset to download
        :param output: file path to where the asset should be saved
        :param tag_substring: substring the release's tag name must contain
        :param use_unstable: if `False`, pre-releases will not be included
        """
        release = self._get_latest_release(tag_substring, content_type, use_unstable)
        if not release:
            raise AssetNotFound(
                f"Could not find release. "
                f"repo={self.repo_name}, tag_substring={tag_substring}"
            )

        asset = self._get_asset(release, content_type, asset_name)
        if not asset:
            raise AssetNotFound(
                f"Could not find asset. "
                f"content_type={content_type}, asset_name={asset_name}"
            )

        logger.debug("Found matching asset. name=%s", asset["name"])
        logger.debug("asset=%s", json.dumps(asset))

        asset_id = str(asset["id"])
        cache_path = self._cache_get(asset_id)
        if cache_path:
            cache_path = cache_path / asset["name"]
            logger.info("Using cached release. cache_path=%s", cache_path)
        else:
            cache_path = self._download_asset(asset)

        if output:
            shutil.copy2(cache_path, output)
            logger.debug("Copied release to output path. output=%s", str(output))

        return output or cache_path
