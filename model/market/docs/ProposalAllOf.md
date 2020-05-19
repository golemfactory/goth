# ProposalAllOf

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**proposal_id** | **str** |  | [optional] [readonly] 
**issuer_id** | **str** |  | [optional] [readonly] 
**state** | **str** | * &#x60;Initial&#x60; - proposal arrived from the market as response to subscription * &#x60;Draft&#x60; - bespoke counter-proposal issued by one party directly to other party (negotiation phase) * &#x60;Rejected&#x60; by other party * &#x60;Accepted&#x60; - promoted into the Agreement draft * &#x60;Expired&#x60; - not accepted nor rejected before validity period  | [optional] [readonly] 
**prev_proposal_id** | **str** | id of the proposal from other side which this proposal responds to  | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


