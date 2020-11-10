"""Module responsible for building the yagna Docker image for testing."""

from dataclasses import asdict, dataclass
import logging
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from typing import List, Optional

from goth.project import DOCKER_DIR, PROJECT_ROOT
from goth.runner.container.yagna import YagnaContainer
from goth.runner.download import (
    ArtifactDownloader,
    ReleaseDownloader,
    ENV_API_TOKEN,
)
from goth.runner.process import run_command

logger = logging.getLogger(__name__)

DOCKERFILE_PATH = DOCKER_DIR / f"{YagnaContainer.IMAGE}.Dockerfile"

EXPECTED_BINARIES = {
    "exe-unit",
    "golemsp",
    "ya-provider",
    "ya-requestor",
    "ya_sb_router",
    "yagna",
}

PROXY_IMAGE = "proxy-nginx"


@dataclass(frozen=True)
class YagnaBuildEnvironment:
    """Configuration for the Docker build process of a yagna image."""

    binary_path: Optional[Path]
    """Local path to directory or archive with binaries to be included in the image."""
    branch: Optional[str]
    """git branch in yagna repo for which to download binaries."""
    commit_hash: Optional[str]
    """git commit hash in yagna repo for which to download binaries."""
    deb_path: Optional[Path]
    """Local path to .deb file or dir with .deb files to be installed in the image."""


async def build_proxy_image() -> None:
    """Build the proxy-nginx Docker image."""

    with TemporaryDirectory() as temp_path:
        build_dir = Path(temp_path)

        required_files = (
            Path("goth", "api_monitor", "nginx.conf"),
            Path("goth", "address.py"),
        )

        for path in required_files:
            if path.parent != Path():
                (build_dir / path.parent).mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT_ROOT / path, build_dir / path)

        proxy_dockerfile = DOCKER_DIR / f"{PROXY_IMAGE}.Dockerfile"
        shutil.copy2(proxy_dockerfile, build_dir / "Dockerfile")

        logger.info(
            "Building %s Docker image. dockerfile=%s, build dir=%s",
            PROXY_IMAGE,
            proxy_dockerfile,
            build_dir,
        )
        command = ["docker", "build", "-t", PROXY_IMAGE, str(build_dir)]
        await run_command(command)


async def build_yagna_image(environment: YagnaBuildEnvironment) -> None:
    """Build the yagna Docker image."""

    with TemporaryDirectory() as temp_path:
        temp_dir = Path(temp_path)
        _setup_build_context(temp_dir, environment)

        logger.info(
            "Building %s Docker image. dockerfile=%s, build dir=%s",
            YagnaContainer.IMAGE,
            DOCKERFILE_PATH,
            temp_dir,
        )
        command = ["docker", "build", "-t", YagnaContainer.IMAGE, str(temp_dir)]
        await run_command(command)


def _download_artifact(env: YagnaBuildEnvironment, download_path: Path) -> None:
    downloader = ArtifactDownloader(token=os.environ.get(ENV_API_TOKEN))
    kwargs = {}

    if env.branch:
        kwargs["branch"] = env.branch
    if env.commit_hash:
        kwargs["commit"] = env.commit_hash

    downloader.download(artifact_name="Yagna Linux", output=download_path, **kwargs)


def _download_release(download_path: Path, repo: str, tag_substring: str = "") -> None:
    downloader = ReleaseDownloader(
        repo=repo, tag_substring=tag_substring, token=os.environ.get(ENV_API_TOKEN)
    )
    downloader.download(output=download_path)


def _find_expected_binaries(root_path: Path) -> List[Path]:
    binary_paths: List[Path] = []

    for root, dirs, files in os.walk(root_path):
        for f in files:
            if f in EXPECTED_BINARIES:
                binary_paths.append(Path(f"{root}/{f}"))

    assert len(binary_paths) == len(EXPECTED_BINARIES)
    return binary_paths


def _setup_build_context(context_dir: Path, env: YagnaBuildEnvironment) -> None:
    """Set up the build context for `docker build` command.

    This function prepares a directory to be used as build context for
    yagna-goth.Dockerfile. This includes copying the original Dockerfile and creating
    two directories: `bin` and `deb`. Depending on the build environment, these will be
    populated with assets from either the local filesystem or downloaded from GitHub.
    """
    env_dict: dict = asdict(env)
    filtered_env = {k: v for k, v in env_dict.items() if v is not None}
    logger.info(
        "Setting up Docker build context. path=%s, env=%s", context_dir, filtered_env
    )

    context_binary_dir: Path = context_dir / "bin"
    context_deb_dir: Path = context_dir / "deb"
    context_binary_dir.mkdir()
    context_deb_dir.mkdir()

    if env.binary_path:
        if env.binary_path.is_dir():
            logger.info("Using local yagna binaries. path=%s", env.binary_path)
            binary_paths = _find_expected_binaries(env.binary_path)
            logger.debug("Found expected yagna binaries. paths=%s", binary_paths)
            for path in binary_paths:
                shutil.copy2(path, context_binary_dir)
        elif env.binary_path.is_file():
            logger.info("Using local yagna archive. path=%s", env.binary_path)
            shutil.unpack_archive(env.binary_path, extract_dir=str(context_binary_dir))
    else:
        _download_artifact(env, context_binary_dir)

    if env.deb_path:
        if env.deb_path.is_dir():
            logger.info("Using local .deb packages. path=%s", env.deb_path)
            shutil.copytree(env.deb_path, context_deb_dir, dirs_exist_ok=True)
        elif env.deb_path.is_file():
            logger.info("Using local .deb package. path=%s", env.deb_path)
            shutil.copy2(env.deb_path, context_deb_dir)
    else:
        _download_release(context_deb_dir, "ya-runtime-wasi")
        _download_release(context_deb_dir, "ya-runtime-vm", "v0.2.1")

    logger.debug(
        "Copying Dockerfile. source=%s, destination=%s", DOCKERFILE_PATH, context_dir
    )
    shutil.copy2(DOCKERFILE_PATH, context_dir / "Dockerfile")
