import logging
from pathlib import Path
import re

from src.runner import Runner
from src.runner.node import Node, Role
from src.runner.scenario import Scenario

logger = logging.getLogger(__name__)


class TestLevel1:
    def test_level1(self, assets_path: Path):

        ## Setup/config

        topology = [
            { "Req1", Requestor, {"SOME_ENV_VARIABLE", "some value"} },
            { "Req2", Requestor, }, ## do no start this node upfront (build probe, but allow to start later)
            { "ProvA", Provider, },  ## Provider A
            { "ProvB", Provider, },  ## Provider B
        ]

        ## Temporal Assertions

        assertions = [
            { assert_no_api_errors, [] }, ## all nodes
            { assert_every_call_gets_response, ["Req1", "Req2"] },  ##  
            { assert_first_call_is_import_key, ["Prov*"] },  ## all nodes starting with "Prov"
            { assert_provider_periodically_collects_demands, [] }, 
        ]

        ## Test scenario setup

        runner = Runner(topology, assertions)

        test_env = runner.run()     ## this instantiates the nodes, creates AssertExecutor 
                                    ## and attaches the probes' even streams to AssertExecutor

        test_env \
            .nodes("Prov*") \
            .start_all()        ## Get all nodes starting with "Prov" and start them

        req1 = test_env.probes[1] ## Reuqestor node probe
        req2 = test_env.probes[2] 
        
        req1.start() ## start the node at required time
        req2.start() ## start the node at required time
        req1.start() ## start the node at required time

        prov_a = test_env.probes[3] ## Provider A

        prov_a.events   ## refer to event stream from this particular node

        ## Test scenario body

        # Payment Init...
    	req1.cli.payment.init(...)
	
	    # allocation (1 GNT, for 1hr, no deposit)
	    req1.payment.create_allocation(1, getdate()+1hr, false)

        # create Demand (and subscribe)
        demand = Demand(
            properties = {
                "golem.srv.comp.wasm.task_package": 
                    "hash://sha3:38D951E2BD2408D95D8D5E5068A69C60C8238FA45DB8BC841DC0BD50:http://34.244.4.185:8000/rust-wasi-tutorial.zip"
            },
            constraints = "(&
                (golem.inf.mem.gib>0.5)
                (golem.inf.storage.gib>1)
                (golem.com.pricing.model=linear)
            )"
        );

        subscriptionId = req1.market.subscribe(demand)

        # receive offer proposals with provider IDs

        offerProposal = req1.market.collect(subscriptionId).firstOrDefault() 

        assertTrue(offerProposal != null)
        assertEqual(offerProposal.issuerId, provider.nodeId)












class Level1Scenario(Scenario):
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
