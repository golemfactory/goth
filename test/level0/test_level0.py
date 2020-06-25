import logging
from pathlib import Path
import re
from string import Template
from typing import Dict, Optional

import pytest

from goth.address import (
    ACTIVITY_API_URL,
    MARKET_API_URL,
    MARKET_BASE_URL,
    PAYMENT_API_URL,
    PROXY_HOST,
    ROUTER_HOST,
    ROUTER_PORT,
    YAGNA_BUS_URL,
    YAGNA_REST_URL,
)
from goth.assertions import EventStream
from goth.runner import Runner
from goth.runner.container.proxy import ProxyContainerConfig
from goth.runner.container.yagna import YagnaContainerConfig
from goth.runner.log_monitor import LogEvent
from goth.runner.probe import Probe, Role
from goth.runner.scenario import Scenario

LogEvents = EventStream[LogEvent]
logger = logging.getLogger(__name__)


def node_environment(
    market_url_base: str = "", rest_api_url_base: str = ""
) -> Dict[str, str]:
    """Construct an environment for executing commands in a yagna docker container."""
    # Use custom base if given, default otherwise
    market_template_params = {"base": market_url_base} if market_url_base else {}

    daemon_env = {
        "CENTRAL_MARKET_URL": MARKET_API_URL.substitute(market_template_params),
        "CENTRAL_NET_HOST": f"{ROUTER_HOST}:{ROUTER_PORT}",
        "GSB_URL": YAGNA_BUS_URL.substitute(host="0.0.0.0"),
        "YAGNA_API_URL": YAGNA_REST_URL.substitute(host="0.0.0.0"),
    }
    node_env = daemon_env

    if rest_api_url_base:
        agent_env = {
            "YAGNA_MARKET_URL": MARKET_API_URL.substitute(base=rest_api_url_base),
            "YAGNA_ACTIVITY_URL": ACTIVITY_API_URL.substitute(base=rest_api_url_base),
            "YAGNA_PAYMENT_URL": PAYMENT_API_URL.substitute(base=rest_api_url_base),
        }
        node_env.update(agent_env)

    return node_env


def assert_message_starts_with(needle: str):
    """Prepare an assertion that:
    Assert that a `LogEvent` with message starts with {needle} is found."""

    # No need to add ^ in the regexp since .match( searches from the start
    pattern = re.compile(needle)

    async def _assert_starts_with(stream: LogEvents):

        async for event in stream:
            match = pattern.match(event.message)
            if match:
                return True

        raise AssertionError(f"No message starts with '{needle}'")

    return _assert_starts_with


async def assert_message_starts_with_and_wait(probe, needle):

    probe.agent_logs.add_assertions([assert_message_starts_with(needle)])
    await probe.agent_logs.await_assertions()


VOLUMES = {
    Template("$assets_path"): "/asset",
    Template("$assets_path/presets.json"): "/presets.json",
}


PROXY_VOLUMES = {
    Template("$assets_path/assertions"): "/assertions",
}


class Level0Scenario(Scenario):
    @property
    def topology(self):
        return [
            ProxyContainerConfig(
                name="proxy", stop_on_error=True, volumes=PROXY_VOLUMES
            ),
            YagnaContainerConfig(
                name="requestor",
                role=Role.requestor,
                environment=node_environment(),
                volumes=VOLUMES,
            ),
            YagnaContainerConfig(
                name="provider_1",
                role=Role.provider,
                environment=node_environment(),
                volumes=VOLUMES,
            ),
            YagnaContainerConfig(
                name="provider_2",
                role=Role.provider,
                # Configure the second provider node to communicate via proxy
                environment=node_environment(
                    market_url_base=MARKET_BASE_URL.substitute(host=PROXY_HOST),
                    rest_api_url_base=YAGNA_REST_URL.substitute(host=PROXY_HOST),
                ),
                volumes=VOLUMES,
            ),
        ]

    @property
    def steps(self):
        return [
            (self.wait_for_offer_subscribed, Role.provider),
            (self.wait_for_proposal_accepted, Role.provider),
            (self.wait_for_agreement_approved, Role.provider),
            (self.wait_for_exeunit_started, Role.provider),
            (self.wait_for_exeunit_finished, Role.provider),
            (self.wait_for_invoice_sent, Role.provider),
        ]

    async def wait_for_offer_subscribed(self, probe: Probe):
        logger.info("waiting for offer to be subscribed")
        await assert_message_starts_with_and_wait(probe, "Subscribed offer")

    async def wait_for_proposal_accepted(self, probe: Probe):
        logger.info("waiting for proposal to be accepted")
        await assert_message_starts_with_and_wait(probe, "Decided to AcceptProposal")
        logger.info("proposal accepted")

    async def wait_for_agreement_approved(self, probe: Probe):
        logger.info("waiting for agreement to be approved")
        await assert_message_starts_with_and_wait(probe, "Decided to ApproveAgreement")
        logger.info("agreement approved")

    async def wait_for_exeunit_started(self, probe: Probe):
        logger.info("waiting for exe-unit to start")
        await assert_message_starts_with_and_wait(probe, r"\[ExeUnit\](.+)Started$")
        logger.info("exe-unit started")

    async def wait_for_exeunit_finished(self, probe: Probe):
        logger.info("waiting for exe-unit to finish")
        await assert_message_starts_with_and_wait(
            probe, "ExeUnit process exited with status Finished - exit code: 0"
        )
        logger.info("exe-unit finished")

    async def wait_for_invoice_sent(self, probe: Probe):
        logger.info("waiting for invoice to be sent")
        await assert_message_starts_with_and_wait(probe, r"Invoice (.+) sent")
        logger.info("invoice sent")


class TestLevel0:
    @pytest.mark.asyncio
    async def test_level0(
        self, api_monitor_image, assets_path: Optional[Path], logs_path: Path
    ):
        await Runner(assets_path, logs_path).run_scenario(Level0Scenario())
