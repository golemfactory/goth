import abc
import logging
import re
from typing import Callable, Dict, List, Tuple

from src.runner.node import Node, Role

logger = logging.getLogger(__name__)


class Scenario(abc.ABC):
    @property
    @abc.abstractmethod
    def nodes(self) -> Dict[Role, int]:
        """ Defines what nodes should be started before the test scenario is run.
            Keys in the dictionary are node roles, values are counts of instances
            to be started. """

    @property
    @abc.abstractmethod
    def steps(self) -> List[Tuple[Callable, Role]]:
        """ List of steps to be executed as part of this test scenario. A single entry
            in the list is a tuple in which the first element is the function to be called
            and the second element specifies which nodes to run the function on. """

    def create_app_key(self, node: Node, key_name: str = "test-key"):
        logger.info("attempting to create app-key. key_name=%s", key_name)
        key = node.create_app_key(key_name)
        logger.info("app-key created: %s", key)

    def start_provider_agent(
        self, node: Node, preset_name: str = "amazing-offer",
    ):
        logger.info("starting provider agent")
        node.start_provider_agent(preset_name)
        node.agent_logs.wait_for_pattern(re.compile(r"^(.+)Subscribed offer.(.+)$"))

    def start_requestor_agent(self, node: Node):
        logger.info("starting requestor agent")
        node.start_requestor_agent()


class Level0Scenario(Scenario):
    nodes = {
        Role.requestor: 1,
        Role.provider: 2,
    }

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

    def wait_for_proposal_accepted(self, node: Node):
        logger.info("waiting for proposal to be accepted")
        node.agent_logs.wait_for_pattern(
            re.compile(r"^(.+)Decided to AcceptProposal(.+)$")
        )
        logger.info("proposal accepted")

    def wait_for_agreement_approved(self, node: Node):
        logger.info("waiting for agreement to be approved")
        node.agent_logs.wait_for_pattern(
            re.compile(r"^(.+)Decided to ApproveAgreement(.+)$")
        )
        logger.info("agreement approved")

    def wait_for_exeunit_started(self, node: Node):
        logger.info("waiting for exe-unit to start")
        node.agent_logs.wait_for_pattern(re.compile(r"^\[ExeUnit\](.+)Started$"))
        logger.info("exe-unit started")

    def wait_for_exeunit_finished(self, node: Node):
        logger.info("waiting for exe-unit to finish")
        node.agent_logs.wait_for_pattern(
            re.compile(
                r"^(.+)ExeUnit process exited with status Finished - exit code: 0(.+)$"
            )
        )
        logger.info("exe-unit finished")

    def wait_for_invoice_sent(self, node: Node):
        logger.info("waiting for invoice to be sent")
        node.agent_logs.wait_for_pattern(
            re.compile(re.compile(r"^(.+)Invoice(.+)sent for agreement(.+)$"))
        )
        logger.info("invoice sent")
