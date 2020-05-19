# coding: utf-8

"""
    Yagna Market API

     ## Yagna Market The Yagna Market is a core component of the Yagna Network, which enables computational Offers and Demands circulation. The Market is open for all entities willing to buy computations (Demands) or monetize computational resources (Offers). ## Yagna Market API The Yagna Market API is the entry to the Yagna Market through which Requestors and Providers can publish their Demands and Offers respectively, find matching counterparty, conduct negotiations and make an agreement.  This version of Market API conforms with capability level 1 of the <a href=\"https://docs.google.com/document/d/1Zny_vfgWV-hcsKS7P-Kdr3Fb0dwfl-6T_cYKVQ9mkNg\"> Market API specification</a>.  Market API contains two roles: Requestors and Providers which are symmetrical most of the time (excluding agreement phase).   # noqa: E501

    The version of the OpenAPI document: 1.5.2
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import unittest

import openapi_market_client
from openapi_market_client.api.provider_api import ProviderApi  # noqa: E501
from openapi_market_client.rest import ApiException


class TestProviderApi(unittest.TestCase):
    """ProviderApi unit test stubs"""

    def setUp(self):
        self.api = openapi_market_client.api.provider_api.ProviderApi()  # noqa: E501

    def tearDown(self):
        pass

    def test_approve_agreement(self):
        """Test case for approve_agreement

        Approves Agreement proposed by the Reqestor.  # noqa: E501
        """
        pass

    def test_collect_demands(self):
        """Test case for collect_demands

        Reads Market responses to published Offer.  # noqa: E501
        """
        pass

    def test_counter_proposal_offer(self):
        """Test case for counter_proposal_offer

        Responds with a bespoke Offer to received Demand.  # noqa: E501
        """
        pass

    def test_get_agreement(self):
        """Test case for get_agreement

        Fetches agreement with given agreement id.  # noqa: E501
        """
        pass

    def test_get_offers(self):
        """Test case for get_offers

        Fetches all active Offers which have been published by the Provider.  # noqa: E501
        """
        pass

    def test_get_proposal_demand(self):
        """Test case for get_proposal_demand

        Fetches Proposal (Demand) with given id.  # noqa: E501
        """
        pass

    def test_post_query_reply_offers(self):
        """Test case for post_query_reply_offers

        Handles dynamic property query.  # noqa: E501
        """
        pass

    def test_reject_agreement(self):
        """Test case for reject_agreement

        Rejects Agreement proposed by the Requestor.  # noqa: E501
        """
        pass

    def test_reject_proposal_demand(self):
        """Test case for reject_proposal_demand

        Rejects Proposal (Demand).  # noqa: E501
        """
        pass

    def test_subscribe_offer(self):
        """Test case for subscribe_offer

        Publishes Provider capabilities via Offer.  # noqa: E501
        """
        pass

    def test_terminate_agreement(self):
        """Test case for terminate_agreement

        Terminates approved Agreement.  # noqa: E501
        """
        pass

    def test_unsubscribe_offer(self):
        """Test case for unsubscribe_offer

        Stop subscription for previously published Offer.  # noqa: E501
        """
        pass


if __name__ == '__main__':
    unittest.main()
