# coding: utf-8

"""
    Yagna Payment API

     Invoicing and Payments is a fundamental area of Yagna Ecosystem functionality. It includes aspects of communication between Requestor, Provider and a selected Payment Platform, which becomes crucial when Activities are executed in the context of negotiated Agreements. Yagna applications must be able to exercise various payment models, and the Invoicing/Payment-related communication is happening in parallel to Activity control communication. To define functional patterns of Requestor/Provider interaction in this area, Payment API is specified.  An important principle of the Yagna Payment API is that the actual payment transactions are hidden behind the Invoice flow. In other words, a Yagna Application on Requestor side isn’t expected to trigger actual payment transactions. Instead it is expected to receive and accept Invoices raised by the Provider - based on Application’s Invoice Accept notifications, the Payment API implementation orchestrates the payment via a configured Payment platform.  **NOTE: This specification is work-in-progress.**   # noqa: E501

    The version of the OpenAPI document: 1.1.0
    Generated by: https://openapi-generator.tech
"""


import pprint
import re  # noqa: F401

import six

from openapi_payment_client.configuration import Configuration


class InvoiceEvent(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'invoice_id': 'str',
        'timestamp': 'datetime',
        'details': 'object',
        'event_type': 'EventType'
    }

    attribute_map = {
        'invoice_id': 'invoiceId',
        'timestamp': 'timestamp',
        'details': 'details',
        'event_type': 'eventType'
    }

    def __init__(self, invoice_id=None, timestamp=None, details=None, event_type=None, local_vars_configuration=None):  # noqa: E501
        """InvoiceEvent - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._invoice_id = None
        self._timestamp = None
        self._details = None
        self._event_type = None
        self.discriminator = None

        self.invoice_id = invoice_id
        self.timestamp = timestamp
        if details is not None:
            self.details = details
        self.event_type = event_type

    @property
    def invoice_id(self):
        """Gets the invoice_id of this InvoiceEvent.  # noqa: E501


        :return: The invoice_id of this InvoiceEvent.  # noqa: E501
        :rtype: str
        """
        return self._invoice_id

    @invoice_id.setter
    def invoice_id(self, invoice_id):
        """Sets the invoice_id of this InvoiceEvent.


        :param invoice_id: The invoice_id of this InvoiceEvent.  # noqa: E501
        :type: str
        """
        if self.local_vars_configuration.client_side_validation and invoice_id is None:  # noqa: E501
            raise ValueError("Invalid value for `invoice_id`, must not be `None`")  # noqa: E501

        self._invoice_id = invoice_id

    @property
    def timestamp(self):
        """Gets the timestamp of this InvoiceEvent.  # noqa: E501


        :return: The timestamp of this InvoiceEvent.  # noqa: E501
        :rtype: datetime
        """
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        """Sets the timestamp of this InvoiceEvent.


        :param timestamp: The timestamp of this InvoiceEvent.  # noqa: E501
        :type: datetime
        """
        if self.local_vars_configuration.client_side_validation and timestamp is None:  # noqa: E501
            raise ValueError("Invalid value for `timestamp`, must not be `None`")  # noqa: E501

        self._timestamp = timestamp

    @property
    def details(self):
        """Gets the details of this InvoiceEvent.  # noqa: E501


        :return: The details of this InvoiceEvent.  # noqa: E501
        :rtype: object
        """
        return self._details

    @details.setter
    def details(self, details):
        """Sets the details of this InvoiceEvent.


        :param details: The details of this InvoiceEvent.  # noqa: E501
        :type: object
        """

        self._details = details

    @property
    def event_type(self):
        """Gets the event_type of this InvoiceEvent.  # noqa: E501


        :return: The event_type of this InvoiceEvent.  # noqa: E501
        :rtype: EventType
        """
        return self._event_type

    @event_type.setter
    def event_type(self, event_type):
        """Sets the event_type of this InvoiceEvent.


        :param event_type: The event_type of this InvoiceEvent.  # noqa: E501
        :type: EventType
        """
        if self.local_vars_configuration.client_side_validation and event_type is None:  # noqa: E501
            raise ValueError("Invalid value for `event_type`, must not be `None`")  # noqa: E501

        self._event_type = event_type

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, InvoiceEvent):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, InvoiceEvent):
            return True

        return self.to_dict() != other.to_dict()
