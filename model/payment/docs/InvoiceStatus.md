# InvoiceStatus

Accepted status indicates that the Requestor confirms the Amount/Total Amount Due on the Invoice/Debit Note, respectively. The Payment API Implementation is expected to proceed with the orchestration of the payment. Internals of the payment processing (eg. payment processing internal states) are specific to the selected Payment Platform, and must be indicated as an attribute of the Accepted status. However, as they are specific - they shall not be standardized by the Payment API.  A Rejected Invoice/Debit Note can subsequently be Accepted.  An Accepted Invoice/Debit Note cannot be subsequently Rejected.  There is a difference between Paid and Settled - depending on a Payment Platform. Paid indicates that the Requestor has ordered Payments of Total Amount Due as indicated by received/accepted Debit Notes/Invoice. Settled indicates that the Provider has reliably received the Payments. 
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


