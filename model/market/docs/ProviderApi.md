# openapi_market_client.ProviderApi

All URIs are relative to *http://localhost/market-api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**approve_agreement**](ProviderApi.md#approve_agreement) | **POST** /agreements/{agreementId}/approve | Approves Agreement proposed by the Reqestor.
[**collect_demands**](ProviderApi.md#collect_demands) | **GET** /offers/{subscriptionId}/events | Reads Market responses to published Offer.
[**counter_proposal_offer**](ProviderApi.md#counter_proposal_offer) | **POST** /offers/{subscriptionId}/proposals/{proposalId} | Responds with a bespoke Offer to received Demand.
[**get_agreement**](ProviderApi.md#get_agreement) | **GET** /agreements/{agreementId} | Fetches agreement with given agreement id.
[**get_offers**](ProviderApi.md#get_offers) | **GET** /offers | Fetches all active Offers which have been published by the Provider.
[**get_proposal_demand**](ProviderApi.md#get_proposal_demand) | **GET** /offers/{subscriptionId}/proposals/{proposalId} | Fetches Proposal (Demand) with given id.
[**post_query_reply_offers**](ProviderApi.md#post_query_reply_offers) | **POST** /offers/{subscriptionId}/propertyQuery/{queryId} | Handles dynamic property query.
[**reject_agreement**](ProviderApi.md#reject_agreement) | **POST** /agreements/{agreementId}/reject | Rejects Agreement proposed by the Requestor.
[**reject_proposal_demand**](ProviderApi.md#reject_proposal_demand) | **DELETE** /offers/{subscriptionId}/proposals/{proposalId} | Rejects Proposal (Demand).
[**subscribe_offer**](ProviderApi.md#subscribe_offer) | **POST** /offers | Publishes Provider capabilities via Offer.
[**terminate_agreement**](ProviderApi.md#terminate_agreement) | **POST** /agreements/{agreementId}/terminate | Terminates approved Agreement.
[**unsubscribe_offer**](ProviderApi.md#unsubscribe_offer) | **DELETE** /offers/{subscriptionId} | Stop subscription for previously published Offer.


# **approve_agreement**
> approve_agreement(agreement_id, timeout=timeout)

Approves Agreement proposed by the Reqestor.

This is a blocking operation. The call may be aborted by Provider caller code. After the call is aborted or timed out, another `approveAgreement` call can be raised on the same `agreementId`. It returns one of the following options: * `Ok` - Indicates that the approved Agreement has been successfully delivered to the Requestor and acknowledged.   - The Requestor side has been notified about the Provider’s commitment     to the Agreement.   - The Provider is now ready to accept a request to start an Activity     as described in the negotiated agreement.   - The Requestor’s corresponding ConfirmAgreement call returns Ok after     the one on the Provider side.  * `Cancelled` - Indicates that before delivering the approved Agreement, the Requestor has called `cancelAgreement`, thus invalidating the Agreement. The Provider may attempt to return to the Negotiation phase by sending a new Proposal.  **Note**: It is expected from the Provider node implementation to “ring-fence” the resources required to fulfill the Agreement before the ApproveAgreement is sent. However, the resources should not be fully committed until `Ok` response is received from the `approveAgreement` call.  **Note**: Mutually exclusive with `rejectAgreement`. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    agreement_id = 'agreement_id_example' # str | 
timeout = 3.4 # float | How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  (optional)

    try:
        # Approves Agreement proposed by the Reqestor.
        api_instance.approve_agreement(agreement_id, timeout=timeout)
    except ApiException as e:
        print("Exception when calling ProviderApi->approve_agreement: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agreement_id** | **str**|  | 
 **timeout** | **float**| How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  | [optional] 

### Return type

void (empty response body)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Agreement approved. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**409** | Agreement already rejected. |  -  |
**410** | Agreement cancelled by the Requstor. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **collect_demands**
> list[OneOfAgreementEventProposalEventPropertyQueryEvent] collect_demands(subscription_id, timeout=timeout, max_events=max_events)

Reads Market responses to published Offer.

This is a blocking operation. It will not return until there is at least one new event.  **Note**: When `collectDemands` is waiting, simultaneous call to `unsubscribeOffer` on the same `subscriptionId` should result in \"Subscription does not exist\" error returned from `collectDemands`.  **Note**: Specification requires this endpoint to support list of specific Proposal Ids to listen for messages related only to specific Proposals. This is not covered yet. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
timeout = 3.4 # float | How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  (optional)
max_events = 56 # int | Maximum number of events that server should return at once (empty value means no limit).  (optional)

    try:
        # Reads Market responses to published Offer.
        api_response = api_instance.collect_demands(subscription_id, timeout=timeout, max_events=max_events)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->collect_demands: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 
 **timeout** | **float**| How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  | [optional] 
 **max_events** | **int**| Maximum number of events that server should return at once (empty value means no limit).  | [optional] 

### Return type

[**list[OneOfAgreementEventProposalEventPropertyQueryEvent]**](OneOfAgreementEventProposalEventPropertyQueryEvent.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Proposal or Agreement event list. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **counter_proposal_offer**
> str counter_proposal_offer(subscription_id, proposal_id, proposal)

Responds with a bespoke Offer to received Demand.

Creates and sends a modified version of original Offer (a counter-proposal) adjusted to previously received Proposal (ie. Demand). Changes Proposal state to `Draft`. Returns created Proposal id. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
proposal_id = 'proposal_id_example' # str | 
proposal = openapi_market_client.Proposal() # Proposal | 

    try:
        # Responds with a bespoke Offer to received Demand.
        api_response = api_instance.counter_proposal_offer(subscription_id, proposal_id, proposal)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->counter_proposal_offer: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 
 **proposal_id** | **str**|  | 
 **proposal** | [**Proposal**](Proposal.md)|  | 

### Return type

**str**

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Counter Proposal created. |  -  |
**400** | Bad request. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**410** | Proposal rejected. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_agreement**
> Agreement get_agreement(agreement_id)

Fetches agreement with given agreement id.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    agreement_id = 'agreement_id_example' # str | 

    try:
        # Fetches agreement with given agreement id.
        api_response = api_instance.get_agreement(agreement_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_agreement: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agreement_id** | **str**|  | 

### Return type

[**Agreement**](Agreement.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Agreement. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_offers**
> list[OneOfOffer] get_offers()

Fetches all active Offers which have been published by the Provider.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    
    try:
        # Fetches all active Offers which have been published by the Provider.
        api_response = api_instance.get_offers()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_offers: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[OneOfOffer]**](OneOfOffer.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Offer list. |  -  |
**400** | Bad request. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_proposal_demand**
> Proposal get_proposal_demand(subscription_id, proposal_id)

Fetches Proposal (Demand) with given id.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
proposal_id = 'proposal_id_example' # str | 

    try:
        # Fetches Proposal (Demand) with given id.
        api_response = api_instance.get_proposal_demand(subscription_id, proposal_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_proposal_demand: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 
 **proposal_id** | **str**|  | 

### Return type

[**Proposal**](Proposal.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Proposal. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**410** | Proposal rejected. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_query_reply_offers**
> post_query_reply_offers(subscription_id, query_id, body)

Handles dynamic property query.

The Market Matching Mechanism, when resolving the match relation for the specific Demand-Offer pair, is to detect the “dynamic” properties required (via constraints) by the other side. At this point, it is able to query the issuing node for those properties and submit the other side’s requested properties as the context of the query.  **Note**: The property query responses may be submitted in “chunks”, ie. the responder may choose to resolve ‘quick’/lightweight’ properties faster and provide response sooner, while still working on more time-consuming properties in the background. Therefore the response contains both the resolved properties, as well as list of properties which responder knows still require resolution.  **Note**: This method must be implemented for Market API Capability Level 2. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
query_id = 'query_id_example' # str | 
body = None # object | 

    try:
        # Handles dynamic property query.
        api_instance.post_query_reply_offers(subscription_id, query_id, body)
    except ApiException as e:
        print("Exception when calling ProviderApi->post_query_reply_offers: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 
 **query_id** | **str**|  | 
 **body** | **object**|  | 

### Return type

void (empty response body)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | OK, query reply posted. |  -  |
**400** | Bad request. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reject_agreement**
> reject_agreement(agreement_id)

Rejects Agreement proposed by the Requestor.

The Requestor side is notified about the Provider’s decision to reject a negotiated agreement. This effectively stops the Agreement handshake.  **Note**: Mutually exclusive with `approveAgreement`. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    agreement_id = 'agreement_id_example' # str | 

    try:
        # Rejects Agreement proposed by the Requestor.
        api_instance.reject_agreement(agreement_id)
    except ApiException as e:
        print("Exception when calling ProviderApi->reject_agreement: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agreement_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Agreement rejected. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**409** | Agreement already approved. |  -  |
**410** | Agreement cancelled by the Requstor. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reject_proposal_demand**
> reject_proposal_demand(subscription_id, proposal_id)

Rejects Proposal (Demand).

Effectively ends a Negotiation chain - it explicitly indicates that the sender will not create another counter-Proposal. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
proposal_id = 'proposal_id_example' # str | 

    try:
        # Rejects Proposal (Demand).
        api_instance.reject_proposal_demand(subscription_id, proposal_id)
    except ApiException as e:
        print("Exception when calling ProviderApi->reject_proposal_demand: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 
 **proposal_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Proposal rejected. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**410** | Proposal already rejected. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **subscribe_offer**
> str subscribe_offer(offer)

Publishes Provider capabilities via Offer.

Offer object can be considered an \"open\" or public Offer, as it is not directed at a specific Requestor, but rather is sent to the market so that the matching mechanism implementation can associate relevant Demands.  **Note**: it is an \"atomic\" operation, ie. as soon as Subscription is placed, the Offer is published on the market. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    offer = openapi_market_client.Offer() # Offer | 

    try:
        # Publishes Provider capabilities via Offer.
        api_response = api_instance.subscribe_offer(offer)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->subscribe_offer: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **offer** | [**Offer**](Offer.md)|  | 

### Return type

**str**

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Subscribed. |  -  |
**400** | Bad request. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **terminate_agreement**
> terminate_agreement(agreement_id)

Terminates approved Agreement.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    agreement_id = 'agreement_id_example' # str | 

    try:
        # Terminates approved Agreement.
        api_instance.terminate_agreement(agreement_id)
    except ApiException as e:
        print("Exception when calling ProviderApi->terminate_agreement: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agreement_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Agreement terminated. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**409** | Agreement not in Approved state. |  -  |
**410** | Agreement cancelled by the Requstor. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **unsubscribe_offer**
> unsubscribe_offer(subscription_id)

Stop subscription for previously published Offer.

Stop receiving Proposals.  **Note**: this will terminate all pending `collectDemands` calls on this subscription. This implies, that client code should not `unsubscribeOffer` before it has received all expected/useful inputs from `collectDemands`. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_market_client
from openapi_market_client.rest import ApiException
from pprint import pprint
configuration = openapi_market_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/market-api/v1
configuration.host = "http://localhost/market-api/v1"

# Enter a context with an instance of the API client
with openapi_market_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_market_client.ProviderApi(api_client)
    subscription_id = 'subscription_id_example' # str | 

    try:
        # Stop subscription for previously published Offer.
        api_instance.unsubscribe_offer(subscription_id)
    except ApiException as e:
        print("Exception when calling ProviderApi->unsubscribe_offer: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Offer revoked. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**410** | Already unsubscribed. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

