"""Module responsible for building the yagna Docker image for testing."""

from dataclasses import asdict, dataclass
import logging
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from typing import Callable, List, Optional

from goth.project import PROJECT_ROOT
from goth.runner.container.yagna import YagnaContainer
from goth.runner.download import (
    ArtifactDownloader,
    ReleaseDownloader,
    ENV_API_TOKEN,
)
from goth.runner.process import run_command

YAGNA_DOCKERFILE = "yagna-goth.Dockerfile"
YAGNA_DOCKERFILE_DEB = "yagna-goth-deb.Dockerfile"


logger = logging.getLogger(__name__)


EXPECTED_BINARIES = {
    "exe-unit",
    "golemsp",
    "ya-provider",
    "yagna",
}

DEB_RELEASE_REPOS = [
    "ya-service-bus",
    "ya-runtime-wasi",
    "ya-runtime-vm",
]

PROXY_IMAGE = "proxy-nginx"


@dataclass(frozen=True)
class YagnaBuildEnvironment:
    """Configuration for the Docker build process of a yagna image."""

    docker_dir: Path
    """Local path to a directory with Dockerfiles to use for building images."""
    binary_path: Optional[Path] = None
    """Local path to directory or archive with binaries to be included in the image."""
    branch: Optional[str] = None
    """git branch in yagna repo for which to download binaries."""
    commit_hash: Optional[str] = None
    """git commit hash in yagna repo for which to download binaries."""
    deb_path: Optional[Path] = None
    """Local path to .deb file or dir with .deb files to be installed in the image."""
    release_tag: Optional[str] = None
    """Release tag substring used to filter the GitHub release to download."""

    @property
    def is_using_deb(self) -> bool:
        """Return true if this environment is set up to use a .deb yagna release."""
        return not any([self.binary_path, self.branch, self.commit_hash])


async def _build_docker_image(
    image_name: str, dockerfile: Path, setup_context: Callable[[Path], None]
) -> None:
    """Set up a temporary build directory and issue `docker build` command there."""

    with TemporaryDirectory() as temp_path:
        build_dir = Path(temp_path)
        setup_context(build_dir)

        logger.info(
            "Building %s Docker image. dockerfile=%s, build dir=%s",
            image_name,
            dockerfile,
            build_dir,
        )
        command = ["docker", "build", "-t", image_name, str(build_dir)]
        await run_command(command)


async def build_proxy_image(docker_dir: Path) -> None:
    """Build the proxy-nginx Docker image."""

    required_files = (
        Path("goth", "api_monitor", "nginx.conf"),
        Path("goth", "address.py"),
    )
    proxy_dockerfile = docker_dir / f"{PROXY_IMAGE}.Dockerfile"

    def _setup_context(build_dir: Path) -> None:
        nonlocal proxy_dockerfile
        for path in required_files:
            (build_dir / path.parent).mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT_ROOT / path, build_dir / path)
        shutil.copy2(proxy_dockerfile, build_dir / "Dockerfile")

    await _build_docker_image(PROXY_IMAGE, proxy_dockerfile, _setup_context)


async def build_yagna_image(environment: YagnaBuildEnvironment) -> None:
    """Build the yagna Docker image."""

    docker_dir = environment.docker_dir
    dockerfile = docker_dir / (
        YAGNA_DOCKERFILE_DEB if environment.is_using_deb else YAGNA_DOCKERFILE
    )

    await _build_docker_image(
        YagnaContainer.IMAGE,
        dockerfile,
        lambda build_dir: _setup_build_context(build_dir, environment, dockerfile),
    )


def _download_artifact(env: YagnaBuildEnvironment, download_path: Path) -> None:
    downloader = ArtifactDownloader(token=os.environ.get(ENV_API_TOKEN))
    kwargs = {}

    if env.branch:
        kwargs["branch"] = env.branch
    if env.commit_hash:
        kwargs["commit"] = env.commit_hash

    downloader.download(artifact_name="Yagna Linux", output=download_path, **kwargs)


def _download_release(
    download_path: Path, repo: str, tag_substring: str = "", asset_name: str = ""
) -> None:
    downloader = ReleaseDownloader(repo=repo, token=os.environ.get(ENV_API_TOKEN))
    downloader.download(
        output=download_path, asset_name=asset_name, tag_substring=tag_substring
    )


def _find_expected_binaries(root_path: Path) -> List[Path]:
    binary_paths: List[Path] = []

    for root, dirs, files in os.walk(root_path):
        for f in files:
            if f in EXPECTED_BINARIES:
                binary_paths.append(Path(f"{root}/{f}"))

    found = {p.name for p in set(binary_paths)}
    missing = EXPECTED_BINARIES - found

    if len(missing) > 0:
        raise RuntimeError(
            f"Failed to find all binaries required to build a yagna Docker image. "
            f"root_path={root_path}, missing_binaries={missing}"
        )

    return binary_paths


def _setup_build_context(
    context_dir: Path, env: YagnaBuildEnvironment, dockerfile: Path
) -> None:
    """Set up the build context for `docker build` command.

    This function prepares a directory to be used as build context for
    building yagna image. This includes copying the original Dockerfile and creating
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

    if env.branch or env.commit_hash:
        _download_artifact(env, context_binary_dir)
    elif env.binary_path:
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
        logger.info("Using yagna release. tag_substring=%s", env.release_tag)
        _download_release(context_deb_dir, "yagna", env.release_tag or "", "provider")

    if env.deb_path:
        if env.deb_path.is_dir():
            logger.info("Using local .deb packages. path=%s", env.deb_path)
            shutil.copytree(env.deb_path, context_deb_dir, dirs_exist_ok=True)
        elif env.deb_path.is_file():
            logger.info("Using local .deb package. path=%s", env.deb_path)
            shutil.copy2(env.deb_path, context_deb_dir)
    else:
        for repo in DEB_RELEASE_REPOS:
            _download_release(context_deb_dir, repo)

    logger.debug(
        "Copying Dockerfile. source=%s, destination=%s", dockerfile, context_dir
    )
    shutil.copy2(dockerfile, context_dir / "Dockerfile")
