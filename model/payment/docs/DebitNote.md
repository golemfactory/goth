# DebitNote

A Debit Note is an artifact issued by the Provider to the Requestor, in the context of a specific Agreement. It is a notification of Total Amount Due incurred by Activities in this Agreement until the moment the Debit Note is issued. This is expected to be used as trigger for payment in upfront-payment or pay-as-you-go scenarios.  NOTE: Debit Notes flag the current Total Amount Due, which is accumulated from the start of Agreement. Debit Notes are expected to trigger payments, therefore payment amount for the newly received Debit Note is expected to be determined by difference of Total Payments for the Agreement vs Total Amount Due. 
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**debit_note_id** | **str** |  | [readonly] 
**issuer_id** | **str** |  | [readonly] 
**recipient_id** | **str** |  | [readonly] 
**payee_addr** | **str** |  | [optional] [readonly] 
**payer_addr** | **str** |  | [optional] [readonly] 
**previous_debit_note_id** | **str** |  | [optional] [readonly] 
**timestamp** | **datetime** |  | [readonly] 
**agreement_id** | **str** |  | [readonly] 
**activity_id** | **str** |  | 
**total_amount_due** | **str** |  | 
**usage_counter_vector** | [**object**](.md) |  | [optional] 
**payment_due_date** | **datetime** |  | [optional] 
**status** | [**InvoiceStatus**](InvoiceStatus.md) |  | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


