import logging
from pathlib import Path
import re
from string import Template

from src.runner import Runner
from src.runner.container.yagna import YagnaContainerConfig
from src.runner.probe import Probe, Role
from src.runner.scenario import Scenario

logger = logging.getLogger(__name__)

ENVIRONMENT_NO_PROXY = {
    "CENTRAL_MARKET_URL": "http://mock-api:5001/market-api/v1/",
    "CENTRAL_NET_HOST": "router:7477",
    "GSB_URL": "tcp://0.0.0.0:6010",
    "YAGNA_API_URL": "http://0.0.0.0:6000",
    "YAGNA_BUS_PORT": "6010",
    "YAGNA_HTTP_PORT": "6000",
}

ENVIRONMENT_WITH_PROXY = ENVIRONMENT_NO_PROXY.copy()
ENVIRONMENT_WITH_PROXY.update(
    {
        # Environment vars used by daemons:
        "CENTRAL_MARKET_URL": "http://proxy:5001/market-api/v1/",
        # Environment vars used by agents:
        "YAGNA_MARKET_URL": "http://proxy:6000/market-api/v1/",
        "YAGNA_ACTIVITY_URL": "http://proxy:6000/activity-api/v1/",
        "YAGNA_PAYMENT_URL": "http://proxy:6000/payment-api/v1/",
    }
)

VOLUMES = {
    Template("$assets_path"): "/asset",
    Template("$assets_path/presets.json"): "/presets.json",
}


class Level0Scenario(Scenario):

    use_proxy: bool
    """Whether to set up environment vars so that API calls are made through proxy"""

    def __init__(self, use_proxy=True):
        self.use_proxy = use_proxy

    @property
    def topology(self):
        environment = ENVIRONMENT_WITH_PROXY if self.use_proxy else ENVIRONMENT_NO_PROXY
        return [
            YagnaContainerConfig(
                name="requestor",
                role=Role.requestor,
                environment=environment,
                volumes=VOLUMES,
            ),
            YagnaContainerConfig(
                name="provider_1",
                role=Role.provider,
                environment=environment,
                volumes=VOLUMES,
            ),
            YagnaContainerConfig(
                name="provider_2",
                role=Role.provider,
                environment=environment,
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
        logger.info("attempting to create app-key. key_name=%s", key_name)
        key = probe.create_app_key(key_name)
        logger.info("app-key created: %s", key)

    def start_provider_agent(
        self, probe: Probe, preset_name: str = "amazing-offer",
    ):
        logger.info("starting provider agent")
        probe.start_provider_agent(preset_name)
        probe.agent_logs.wait_for_pattern(re.compile(r"^(.+)Subscribed offer.(.+)$"))

    def start_requestor_agent(self, probe: Probe):
        logger.info("starting requestor agent")
        probe.start_requestor_agent()

    def wait_for_proposal_accepted(self, probe: Probe):
        logger.info("waiting for proposal to be accepted")
        probe.agent_logs.wait_for_pattern(
            re.compile(r"^(.+)Decided to AcceptProposal(.+)$")
        )
        logger.info("proposal accepted")

    def wait_for_agreement_approved(self, probe: Probe):
        logger.info("waiting for agreement to be approved")
        probe.agent_logs.wait_for_pattern(
            re.compile(r"^(.+)Decided to ApproveAgreement(.+)$")
        )
        logger.info("agreement approved")

    def wait_for_exeunit_started(self, probe: Probe):
        logger.info("waiting for exe-unit to start")
        probe.agent_logs.wait_for_pattern(re.compile(r"^\[ExeUnit\](.+)Started$"))
        logger.info("exe-unit started")

    def wait_for_exeunit_finished(self, probe: Probe):
        logger.info("waiting for exe-unit to finish")
        probe.agent_logs.wait_for_pattern(
            re.compile(
                r"^(.+)ExeUnit process exited with status Finished - exit code: 0(.+)$"
            )
        )
        logger.info("exe-unit finished")

    def wait_for_invoice_sent(self, probe: Probe):
        logger.info("waiting for invoice to be sent")
        probe.agent_logs.wait_for_pattern(
            re.compile(re.compile(r"^(.+)Invoice (.+) sent(.+)$"))
        )
        logger.info("invoice sent")


class TestLevel0:
    def test_level0(self, assets_path: Path, logs_path: Path):
        Runner(assets_path, logs_path).run(Level0Scenario(use_proxy=True))
