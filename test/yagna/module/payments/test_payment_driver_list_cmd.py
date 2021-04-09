"""Tests payment driver list CLI command."""

import logging
from pathlib import Path
from typing import List, Optional

import pytest

from goth.address import (
    PROXY_HOST,
    YAGNA_REST_URL,
)
from goth.node import node_environment
from goth.runner import Runner
from goth.runner.container.payment import PaymentIdPool
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.requestor import RequestorProbeWithApiSteps
from goth.runner.container.build import YagnaBuildEnvironment


logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def yagna_build_env(
    assets_path: Path,
    yagna_binary_path: Optional[Path],
    yagna_branch: Optional[str],
    # yagna_commit_hash: Optional[str],
    deb_package: Optional[Path],
    yagna_release: Optional[str],
) -> YagnaBuildEnvironment:
    """Override the default fixture to force using specific yagna commit."""

    """Fixture which provides the build environment for yagna Docker images."""
    return YagnaBuildEnvironment(
        docker_dir=assets_path / "docker",
        binary_path=yagna_binary_path,
        branch=yagna_branch,
        commit_hash="c4d1dd7",
        deb_path=deb_package,
        release_tag=yagna_release,
    )


def _topology(payment_id_pool: PaymentIdPool) -> List[YagnaContainerConfig]:
    # Nodes are configured to communicate via proxy

    requestor_env = node_environment(
        rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
    )

    return [
        YagnaContainerConfig(
            name="requestor",
            probe_type=RequestorProbeWithApiSteps,
            environment=requestor_env,
            payment_id=payment_id_pool.get_id(),
        ),
    ]


@pytest.mark.asyncio
async def test_payment_driver_list(
    assets_path: Path,
    demand_constraints: str,
    payment_id_pool: PaymentIdPool,
    runner: Runner,
    task_package_template: str,
):
    """Test just the requestor's CLI command, no need to setup provider."""

    topology = _topology(payment_id_pool)

    async with runner(topology):
        requestor = runner.get_probes(probe_type=RequestorProbeWithApiSteps)[0]

        res = requestor.cli.payment_drivers()
        assert res and res.items()
        driver = next(iter(res.values()), None)

        assert driver.default_network, "Default network should be set"

        network = driver.networks.get(driver.default_network, None)
        assert network, "Network should belong to the Driver"
        assert network.default_token, "Default taken should be set"

        token = network.tokens.get(network.default_token, None)
        assert token, "Token should belong to the Network"
