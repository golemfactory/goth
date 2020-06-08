# Invoice

An Invoice is an artifact issued by the Provider to the Requestor, in the context of a specific Agreement. It indicates the total Amount owed by the Requestor in this Agreement. No further Debit Notes shall be issued after the Invoice is issued. The issue of Invoice signals the Termination of the Agreement (if it hasn't been terminated already). No Activity execution is allowed after the Invoice is issued.  NOTE: An invoice can be issued even before any Activity is started in the context of an Agreement (eg. in one off, 'fire-and-forget' payment regime). 
## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**invoice_id** | **str** |  | [readonly] 
**issuer_id** | **str** |  | [readonly] 
**recipient_id** | **str** |  | [readonly] 
**payee_addr** | **str** |  | [optional] [readonly] 
**payer_addr** | **str** |  | [optional] [readonly] 
**last_debit_note_id** | **str** |  | [optional] [readonly] 
**timestamp** | **datetime** |  | [readonly] 
**agreement_id** | **str** |  | 
**activity_ids** | **list[str]** |  | [optional] 
**amount** | **str** |  | 
**payment_due_date** | **datetime** |  | 
**status** | [**InvoiceStatus**](InvoiceStatus.md) |  | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


