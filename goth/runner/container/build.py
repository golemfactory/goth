"""Module responsible for building the yagna Docker image for testing."""

import logging
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional

from goth.project import DOCKER_DIR
from goth.runner.download import (
    ArtifactDownloader,
    ReleaseDownloader,
    ENV_API_TOKEN,
    ENV_YAGNA_BRANCH,
    ENV_YAGNA_COMMIT,
)
from goth.runner.process import run_command

logger = logging.getLogger(__name__)

DOCKERFILE_PATH = DOCKER_DIR / "yagna-goth.Dockerfile"

ENV_YAGNA_BINARY_DIR = "YAGNA_BINARY_DIR"
ENV_YAGNA_DEB_DIR = "YAGNA_DEB_DIR"
ENV_YAGNA_PACKAGE = "YAGNA_PACKAGE"

EXPECTED_BINARIES = set(
    [
        "exe-unit",
        "golemsp",
        "ya-provider",
        "ya-requestor",
        "ya_sb_router",
        "yagna",
    ]
)


async def build(environment: Dict[str, str]):
    """Build the yagna Docker image."""
    with TemporaryDirectory() as temp_path:
        temp_dir = Path(temp_path)
        logger.info("setting up Docker build context. path=%s", temp_dir)
        _setup_build_context(temp_dir, environment)

        logger.info("building Docker image. file=%s", DOCKERFILE_PATH)
        command = ["docker", "build", f"{temp_dir}"]
        await (run_command(command))


def _download_artifact(env: Dict[str, str], download_path: Path):
    downloader = ArtifactDownloader(token=env.get(ENV_API_TOKEN))

    kwargs = {}
    if env.get(ENV_YAGNA_BRANCH):
        kwargs["branch"] = env[ENV_YAGNA_BRANCH]
    if env.get(ENV_YAGNA_COMMIT):
        kwargs["commit"] = env[ENV_YAGNA_COMMIT]

    downloader.download(artifact_name="Yagna Linux", output=download_path, **kwargs)


def _download_release(env: Dict[str, str], download_path: Path):
    downloader = ReleaseDownloader(repo="ya-runtime-wasi", token=env.get(ENV_API_TOKEN))
    downloader.download(output=download_path)


def _find_expected_binaries(root_path: Path) -> List[Path]:
    binary_paths: List[Path] = []

    for root, dirs, files in os.walk(root_path):
        for f in files:
            if f in EXPECTED_BINARIES:
                binary_paths.append(Path(f"{root}/{f}"))

    assert len(binary_paths) == len(EXPECTED_BINARIES)
    return binary_paths


def _setup_build_context(context_dir: Path, environment: Dict[str, str]):
    context_binary_dir: Path = context_dir / "bin"
    context_deb_dir: Path = context_dir / "deb"
    context_binary_dir.mkdir()
    context_deb_dir.mkdir()

    def _resolve_if_exists(env_key: str) -> Optional[Path]:
        env_value: Optional[str] = environment.get(env_key)
        return Path(env_value).resolve() if env_value else None

    local_binary_dir = _resolve_if_exists(ENV_YAGNA_BINARY_DIR)
    local_deb_dir = _resolve_if_exists(ENV_YAGNA_DEB_DIR)
    local_package_path = _resolve_if_exists(ENV_YAGNA_PACKAGE)

    if local_binary_dir:
        logger.info("using local yagna binaries. path=%s", local_binary_dir)
        binary_paths = _find_expected_binaries(local_binary_dir)
        logger.debug("found expected yagna binaries. paths=%s", binary_paths)
        for path in binary_paths:
            shutil.copy2(path, context_binary_dir)
    elif local_package_path:
        logger.info("using local yagna package. path=%s", local_package_path)
        shutil.unpack_archive(local_package_path, extract_dir=str(context_binary_dir))
    else:
        _download_artifact(environment, context_binary_dir)

    if local_deb_dir:
        logger.info("using local .deb packages. path=%s", local_deb_dir)
        shutil.copytree(local_deb_dir, context_deb_dir, dirs_exist_ok=True)
    else:
        _download_release(environment, context_deb_dir)

    logger.debug(
        "copying Dockerfile. source=%s, destination=%s", DOCKERFILE_PATH, context_dir
    )
    shutil.copy2(DOCKERFILE_PATH, context_dir / "Dockerfile")
