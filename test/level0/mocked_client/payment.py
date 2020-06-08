import os
import time

from openapi_payment_client import (
    ApiClient,
    Configuration,
    RequestorApi,
    Acceptance,
    Allocation,
)


def level0_payment(agreement_id):
    # INIT
    config = Configuration(host=f"{os.environ['YAGNA_API_URL']}/payment-api/v1")
    config.access_token = os.environ["APP_KEY"]

    req_api = RequestorApi(ApiClient(config))
    print(f"Init completed, connected to {config.host}")
    # v. PROVIDER

    # provider.events.waitUntil(LogEvent, event => event.message matches "DestroyActivity regexp")

    # 8. REQUESTOR
    invoice_events = []
    while len(invoice_events) == 0:
        time.sleep(2.0)
        invoice_events = (
            req_api.get_received_invoices()
        )  # to be replaced by requestor.events.waitUntil(InvoiceReceivedEvent)
        print(f"Gathered invoice_event {invoice_events}")
        invoice_events = list(
            filter(lambda x: x.agreement_id == agreement_id, invoice_events)
        )
        print(f"filtered invoice_event {invoice_events}")

    invoice_event = invoice_events[0]

    allocation = Allocation(
        total_amount=invoice_event.amount,
        spent_amount=0,
        remaining_amount=0,
        make_deposit=True,
    )
    allocation_result = req_api.create_allocation(allocation)
    print(f"Created allocation. id={allocation_result}")

    acceptance = Acceptance(
        total_amount_accepted=invoice_event.amount,
        allocation_id=allocation_result.allocation_id,
    )
    req_api.accept_invoice(invoice_event.invoice_id, acceptance)
    print(f"Accepted invoice. id={invoice_event.invoice_id}")

    # 9. PROVIDER

    # provider.events.waitUntil(LogEvent, event => event.message matches "Payment received regexp")

    # ... and maybe we can assert some balance change on etherscan???
