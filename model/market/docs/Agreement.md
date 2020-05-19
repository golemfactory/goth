# Agreement

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**agreement_id** | **str** |  | 
**demand** | [**Demand**](Demand.md) |  | 
**offer** | [**Offer**](Offer.md) |  | 
**valid_to** | **datetime** | End of validity period. Agreement needs to be accepted, rejected or cancellled before this date; otherwise will expire  | 
**approved_date** | **datetime** | date of the Agreement approval | [optional] 
**state** | **str** | * &#x60;Proposal&#x60; - newly created by a Requestor (based on Proposal) * &#x60;Pending&#x60; - confirmed by a Requestor and send to Provider for approval * &#x60;Cancelled&#x60; by a Requestor * &#x60;Rejected&#x60; by a Provider * &#x60;Approved&#x60; by both sides * &#x60;Expired&#x60; - not accepted, rejected nor cancelled within validity period * &#x60;Terminated&#x60; - finished after approval.  | 
**proposed_signature** | **str** |  | [optional] 
**approved_signature** | **str** |  | [optional] 
**committed_signature** | **str** |  | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


