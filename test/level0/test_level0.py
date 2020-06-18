import logging
from pathlib import Path
import re
from string import Template
from typing import Dict, Optional

import pytest

from src.runner.log_monitor import APIEvent
from src.assertions import EventStream
from src.runner import Runner
from src.runner.container.proxy import ProxyContainerConfig
from src.runner.container.yagna import YagnaContainerConfig
from src.runner.log_monitor import LogEvent
from src.runner.probe import Probe, Role
from src.runner.scenario import Scenario

# TODO: Remove duplicate with test.level0.assertions.common_assertions.py
APIEvents = EventStream[APIEvent]

logger = logging.getLogger(__name__)


YAGNA_BUS_PORT = 6010
YAGNA_HTTP_PORT = 6000
ROUTER_ADDRESS = "router:7477"


def node_environment(
    market_url_base: str = "http://mock-api:5001", rest_api_url_base: str = ""
) -> Dict[str, str]:
    """Construct an environment for executing commands in a yagna docker container."""

    daemon_env = {
        "CENTRAL_MARKET_URL": f"{market_url_base}/market-api/v1/",
        "CENTRAL_NET_HOST": ROUTER_ADDRESS,
        "GSB_URL": f"tcp://0.0.0.0:{YAGNA_BUS_PORT}",
        "YAGNA_API_URL": f"http://0.0.0.0:{YAGNA_HTTP_PORT}",
    }
    node_env = daemon_env

    if rest_api_url_base:
        agent_env = {
            "YAGNA_MARKET_URL": f"{rest_api_url_base}/market-api/v1/",
            "YAGNA_ACTIVITY_URL": f"{rest_api_url_base}/activity-api/v1/",
            "YAGNA_PAYMENT_URL": f"{rest_api_url_base}/payment-api/v1/",
        }
        node_env.update(agent_env)

    return node_env


def assert_message_starts_with(needle: str):
    """Prepare an assertion that:
    Assert that a `LogEvent` with message starts with {needle} is found."""

    pattern = re.compile(r"^" + needle)

    async def _assert_starts_with(stream: APIEvents):

        async for event in stream:

            if isinstance(event, LogEvent):
                has_match = pattern.match(event.message)
                pattern.purge()
                if has_match:
                    return True

        return False

    return _assert_starts_with


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
                    market_url_base="http://proxy:5001",
                    rest_api_url_base="http://proxy:6000",
                ),
                volumes=VOLUMES,
            ),
        ]

    @property
    def steps(self):
        return [
            (self.create_app_key, Role.requestor),
            (self.create_app_key, Role.provider),
            (self.start_provider_agent, Role.provider),
            (self.start_requestor_agent, Role.requestor),
            (self.wait_for_proposal_accepted, Role.provider),
            (self.wait_for_agreement_approved, Role.provider),
            (self.wait_for_exeunit_started, Role.provider),
            (self.wait_for_exeunit_finished, Role.provider),
            (self.wait_for_invoice_sent, Role.provider),
        ]

    def create_app_key(self, probe: Probe, key_name: str = "test-key"):
        key = probe.create_app_key(key_name)
        logger.info("app-key created. name=%s key=%s", key_name, key)

    async def start_provider_agent(
        self, probe: Probe, preset_name: str = "amazing-offer",
    ):
        logger.info("starting provider agent")
        probe.start_provider_agent(preset_name)
        probe.agent_logs.add_assertions(
            [assert_message_starts_with("Subscribed offer")]
        )
        await probe.agent_logs.await_assertions()

    def start_requestor_agent(self, probe: Probe):
        logger.info("starting requestor agent")
        probe.start_requestor_agent()

    async def wait_for_proposal_accepted(self, probe: Probe):
        logger.info("waiting for proposal to be accepted")
        probe.agent_logs.add_assertions(
            [assert_message_starts_with("Decided to AcceptProposal")]
        )
        await probe.agent_logs.await_assertions()
        logger.info("proposal accepted")

    async def wait_for_agreement_approved(self, probe: Probe):
        logger.info("waiting for agreement to be approved")
        probe.agent_logs.add_assertions(
            [assert_message_starts_with("Decided to ApproveAgreement")]
        )
        await probe.agent_logs.await_assertions()
        logger.info("agreement approved")

    async def wait_for_exeunit_started(self, probe: Probe):
        logger.info("waiting for exe-unit to start")
        probe.agent_logs.add_assertions(
            [assert_message_starts_with(r"\[ExeUnit\](.+)Started$")]
        )
        await probe.agent_logs.await_assertions()
        logger.info("exe-unit started")

    async def wait_for_exeunit_finished(self, probe: Probe):
        logger.info("waiting for exe-unit to finish")
        probe.agent_logs.add_assertions(
            [
                assert_message_starts_with(
                    "ExeUnit process exited with status Finished - exit code: 0"
                )
            ]
        )
        await probe.agent_logs.await_assertions()
        logger.info("exe-unit finished")

    async def wait_for_invoice_sent(self, probe: Probe):
        logger.info("waiting for invoice to be sent")
        probe.agent_logs.add_assertions(
            [assert_message_starts_with("Invoice (.+) sent")]
        )
        await probe.agent_logs.await_assertions()
        logger.info("invoice sent")


class TestLevel0:
    @pytest.mark.asyncio
    async def test_level0(
        self, api_monitor_image, assets_path: Optional[Path], logs_path: Path
    ):
        await Runner(assets_path, logs_path).run_scenario(Level0Scenario())
