"""Helper functions for easy handling of payments."""

from typing import List, Tuple

from goth.runner.probe import ProviderProbe, RequestorProbe


async def pay_all(
    requestor: RequestorProbe,
    agreements: List[Tuple[str, ProviderProbe]],
):
    """Pay for all Agreements."""
    for agreement_id, provider in agreements:
        await provider.wait_for_invoice_sent()
        invoices = await requestor.gather_invoices(agreement_id)
        assert all(inv.agreement_id == agreement_id for inv in invoices)
        # TODO:
        await requestor.pay_invoices(invoices)
        await provider.wait_for_invoice_paid()
