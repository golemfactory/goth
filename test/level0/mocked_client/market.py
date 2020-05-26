from datetime import datetime, timedelta
import os
import time
import sys

from openapi_market_client import (
    ApiClient,
    Configuration,
    RequestorApi,
    Demand,
    DemandOfferBase,
    Proposal,
    AgreementProposal,
)


def level0_market():
    # INIT
    config = Configuration(host=os.environ["MARKET_URL_BASE"] + "/market-api/v1")

    config.api_key["Authorization"] = os.environ["APP_KEY"]
    config.api_key_prefix["Authorization"] = "Bearer"

    req_api = RequestorApi(ApiClient(config))
    print(f"Init completed, connected to {config.host}")

    # REGISTER DEMAND
    demand = Demand(
        requestor_id=os.environ["NODE_ID"],
        properties={
            "golem.node.id.name": "test1",
            "golem.srv.comp.expiration": int(
                (datetime.now() + timedelta(days=1)).timestamp() * 1000
            ),
            "golem.srv.comp.wasm.task_package": "hash://sha3:38D951E2BD2408D95D8D5E5068A69C60C8238FA45DB8BC841DC0BD50:http://34.244.4.185:8000/rust-wasi-tutorial.zip",
        },
        constraints="(&(golem.inf.mem.gib>0.5)(golem.inf.storage.gib>1)(golem.com.pricing.model=linear))",
    )
    subscription_id = req_api.subscribe_demand(demand)
    print(f"Subscribe completed, subscription_id={subscription_id}")
    time.sleep(2.0)  # TODO: collect_offers should wait
    # COLLECT OFFERS

    offerProposal = None
    while offerProposal is None:
        result_offers = req_api.collect_offers(subscription_id)
        if len(result_offers):
            offerProposal = result_offers[0].proposal
        else:
            print(f"Waiting on proposal... {result_offers}")
            time.sleep(1.0)

    print(f"Collected offer proposal. proposal={offerProposal}")

    proposal = Proposal(
        constraints=demand.constraints,
        properties=demand.properties,
        prev_proposal_id=offerProposal.proposal_id,
    )

    counter_proposal = req_api.counter_proposal_demand(
        subscription_id=subscription_id,
        proposal_id=offerProposal.proposal_id,
        proposal=proposal,
    )

    print(f"Posted counter proposal. proposal={type(counter_proposal)}")
    time.sleep(2.0)

    # Collect counter proposal reply

    counterProposal = None
    while counterProposal is None:
        result_offers = req_api.collect_offers(subscription_id)
        print(f"result_offers. proposal={result_offers}")
        if len(result_offers):
            counterProposal = result_offers[0].proposal
        else:
            print(f"Waiting on proposal... {result_offers}")
            time.sleep(1.0)

    print(f"Collected offer proposal. proposal={counterProposal}")

    valid_to = str(datetime.utcnow() + timedelta(days=1)) + "Z"
    print(f"valid_to={valid_to}")
    agreement_proposal = AgreementProposal(
        proposal_id=counterProposal.proposal_id, valid_to=valid_to
    )

    agreementId = req_api.create_agreement(agreement_proposal)
    print(f"Created agreement. agreementId={agreementId}")
    time.sleep(2.0)

    result = req_api.confirm_agreement(agreementId)
    print(f"Confirmed agreement. result={result}")
    time.sleep(2.0)

    result = req_api.wait_for_approval(agreementId)
    print(f"Agreement approved. result={result}")

    return agreementId
