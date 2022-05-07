"""Unit tests for goth.api_monitor.api_events module."""
# A large number of flake8 F405 errors due to `import *`
# flake8: noqa
import pytest

from goth.api_monitor.api_events import *


@pytest.mark.parametrize(
    "predicate, method, path, params",
    [
        # ApproveAgreement
        (
            is_approve_agreement,
            "POST",
            "market-api/v1/agreements/{agr_id}/approve",
            {"agr_id": "123-456"},
        ),
        (
            is_approve_agreement,
            "POST",
            "market-api/v1/agreements/{agr_id}/approve?param=1",
            {"agr_id": "123-456"},
        ),
        (
            is_approve_agreement,
            "POST",
            "market-api/v1/agreement/{agr_id}/approve",
            False,
        ),
        (
            is_approve_agreement,
            "POST",
            "market-api/v1/agreements/approve",
            False,
        ),
        (
            is_approve_agreement,
            "POST",
            "market_api/v1/agreements/{agr_id}/approve",
            False,
        ),
        # CollectDemands
        (
            is_collect_demands,
            "GET",
            "market-api/v1/offers/{sub_id}/events",
            {"sub_id": "123-456"},
        ),
        (
            is_collect_demands,
            "GET",
            "market-api/v1/offers/{sub_id}/events?param=1",
            {"sub_id": "123-456"},
        ),
        (is_collect_demands, "GET", "market-api/v1/offers/{sub_id}/event", False),
        # CounterProposalOffer
        (
            is_counter_proposal_offer,
            "POST",
            "market-api/v1/offers/{sub_id}/proposals/{prop_id}",
            {"sub_id": "sub-123", "prop_id": "prop-456"},
        ),
        (
            is_counter_proposal_offer,
            "POST",
            "market-api/v1/offers/{sub_id}/proposals/{prop_id}?param=1",
            {"sub_id": "sub-123", "prop_id": "prop-456"},
        ),
        (
            is_counter_proposal_offer,
            "POST",
            "market-api/v1/offers/{sub_id}/proposal/{prop_id}",
            False,
        ),
        (
            is_counter_proposal_offer,
            "POST",
            "market-api/v1/offers/{sub_id}/proposals",
            False,
        ),
        # CreateAgreement
        (is_create_agreement, "POST", "market-api/v1/agreements", {}),
        (is_create_agreement, "POST", "market-api/v1/agreements?param=1", {}),
        (
            is_create_agreement,
            "POST",
            "market-api/v1/agreement",
            False,
        ),
        # SubscribeOffer
        (is_subscribe_offer, "POST", "market-api/v1/offers", {}),
        (is_subscribe_offer, "POST", "market-api/v1/offers?param=1", {}),
        (is_subscribe_offer, "POST", "market-api/v1/offer", False),
        # UnsubscribeOffer
        (
            is_unsubscribe_offer,
            "DELETE",
            "market-api/v1/offers/{sub_id}",
            {"sub_id": "123-456"},
        ),
        (
            is_unsubscribe_offer,
            "DELETE",
            "market-api/v1/offers/{sub_id}?param=1",
            {"sub_id": "123-456"},
        ),
        (is_unsubscribe_offer, "DELETE", "market-api/v1/offer/{sub_id}", False),
        # Paymenr: GetInvoiceEvents
        (
            is_get_invoice_events,
            "GET",
            "payment-api/v1/invoiceEvents",
            {},
        ),
        (is_get_invoice_events, "GET", "payment-api/v1/invoiceEvents?param=1", {}),
        # Payment: SendInvoice
        (
            is_send_invoice,
            "POST",
            "payment-api/v1/invoices/{inv_id}/send",
            {"inv_id": "123-456"},
        ),
        (
            is_send_invoice,
            "POST",
            "payment-api/v1/invoices/{inv_id}/send?param=1",
            {"inv_id": "123-456"},
        ),
        (is_send_invoice, "POST", "payment-api/v1/invoice/{inv_id}/send", False),
        (is_send_invoice, "POST", "payment-api/v1/invoices/{inv_id}", False),
    ],
)
def test_event_predicates(predicate, method, path, params):

    if params:
        path = path.format(**params)

    http_req = HTTPRequest.make(
        method=method,
        url=f"http://11.22.33.44:5555/{path}",
        content="mock content",
        headers={},
    )
    http_resp = HTTPResponse.make(status_code=200, content="mock content", headers={})

    req = APIRequest(1, http_req)
    resp = APIResponse(req, http_resp)

    if params is False:
        # Test non-matching
        result = predicate(req, event_type=APIRequest)
        assert not result
        result = predicate(resp, event_type=APIResponse)
        assert not result
        return

    # Test with predicate called with expected params
    assert predicate(req, event_type=APIRequest, **params) == (params or True)

    # Test with predicate called without params specified
    assert predicate(req, event_type=APIRequest) == (params or True)

    # Test with predicate called with non-matching params
    different_params = {key: value * 2 for key, value in params.items()}
    if params:
        assert not predicate(req, event_type=APIRequest, **different_params)

    # Repeat tests with predicate called for a response
    assert predicate(resp, event_type=APIResponse, **params) == (params or True)
    assert predicate(resp, event_type=APIResponse) == (params or True)
    if params:
        assert not predicate(resp, event_type=APIResponse, **different_params)

    # Test with non-matching type
    assert not predicate(req, event_type=APIResponse, **params)
    assert not predicate(resp, event_type=APIRequest, **params)

    # Test with different method
    different_method = "GET" if method == "POST" else "POST"
    http_req = HTTPRequest.make(
        method=different_method,
        url=f"http://11.22.33.44:5555/{path}",
        content="mock content",
        headers={},
    )
    http_resp = HTTPResponse.make(status_code=200, content="mock content", headers={})
    req = APIRequest(1, http_req)
    resp = APIResponse(req, http_resp)

    assert not predicate(req, event_type=APIRequest)
    assert not predicate(resp, event_type=APIResponse)
