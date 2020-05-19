# coding: utf-8

"""
    Yagna Payment API

     Invoicing and Payments is a fundamental area of Yagna Ecosystem functionality. It includes aspects of communication between Requestor, Provider and a selected Payment Platform, which becomes crucial when Activities are executed in the context of negotiated Agreements. Yagna applications must be able to exercise various payment models, and the Invoicing/Payment-related communication is happening in parallel to Activity control communication. To define functional patterns of Requestor/Provider interaction in this area, Payment API is specified.  An important principle of the Yagna Payment API is that the actual payment transactions are hidden behind the Invoice flow. In other words, a Yagna Application on Requestor side isn’t expected to trigger actual payment transactions. Instead it is expected to receive and accept Invoices raised by the Provider - based on Application’s Invoice Accept notifications, the Payment API implementation orchestrates the payment via a configured Payment platform.  **NOTE: This specification is work-in-progress.**   # noqa: E501

    The version of the OpenAPI document: 1.1.0
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest
import datetime

import openapi_payment_client
from openapi_payment_client.models.invoice import Invoice  # noqa: E501
from openapi_payment_client.rest import ApiException

class TestInvoice(unittest.TestCase):
    """Invoice unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional):
        """Test Invoice
            include_option is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # model = openapi_payment_client.models.invoice.Invoice()  # noqa: E501
        if include_optional :
            return Invoice(
                invoice_id = '0', 
                issuer_id = '0', 
                recipient_id = '0', 
                payee_addr = '0', 
                payer_addr = '0', 
                last_debit_note_id = '0', 
                timestamp = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'), 
                agreement_id = '0', 
                activity_ids = [
                    '0'
                    ], 
                amount = '0', 
                payment_due_date = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'), 
                status = 'ISSUED'
            )
        else :
            return Invoice(
                invoice_id = '0',
                issuer_id = '0',
                recipient_id = '0',
                timestamp = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'),
                agreement_id = '0',
                amount = '0',
                payment_due_date = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'),
                status = 'ISSUED',
        )

    def testInvoice(self):
        """Test Invoice"""
        inst_req_only = self.make_instance(include_optional=False)
        inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == '__main__':
    unittest.main()
