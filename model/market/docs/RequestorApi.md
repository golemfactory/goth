# openapi_market_client.RequestorApi

All URIs are relative to *http://localhost/market-api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**cancel_agreement**](RequestorApi.md#cancel_agreement) | **DELETE** /agreements/{agreementId} | Cancels agreement.
[**collect_offers**](RequestorApi.md#collect_offers) | **GET** /demands/{subscriptionId}/events | Reads Market responses to published Demand.
[**confirm_agreement**](RequestorApi.md#confirm_agreement) | **POST** /agreements/{agreementId}/confirm | Sends Agreement draft to the Provider.
[**counter_proposal_demand**](RequestorApi.md#counter_proposal_demand) | **POST** /demands/{subscriptionId}/proposals/{proposalId} | Responds with a bespoke Demand to received Offer.
[**create_agreement**](RequestorApi.md#create_agreement) | **POST** /agreements | Creates Agreement from selected Proposal.
[**get_agreement**](RequestorApi.md#get_agreement) | **GET** /agreements/{agreementId} | Fetches agreement with given agreement id.
[**get_demands**](RequestorApi.md#get_demands) | **GET** /demands | Fetches all active Demands which have been published by the Requestor.
[**get_proposal_offer**](RequestorApi.md#get_proposal_offer) | **GET** /demands/{subscriptionId}/proposals/{proposalId} | Fetches Proposal (Offer) with given id.
[**post_query_reply_demands**](RequestorApi.md#post_query_reply_demands) | **POST** /demands/{subscriptionId}/propertyQuery/{queryId} | Handles dynamic property query.
[**reject_proposal_offer**](RequestorApi.md#reject_proposal_offer) | **DELETE** /demands/{subscriptionId}/proposals/{proposalId} | Rejects Proposal (Offer).
[**subscribe_demand**](RequestorApi.md#subscribe_demand) | **POST** /demands | Publishes Requestor capabilities via Demand.
[**terminate_agreement**](RequestorApi.md#terminate_agreement) | **POST** /agreements/{agreementId}/terminate | Terminates approved Agreement.
[**unsubscribe_demand**](RequestorApi.md#unsubscribe_demand) | **DELETE** /demands/{subscriptionId} | Stop subscription for previously published Demand.
[**wait_for_approval**](RequestorApi.md#wait_for_approval) | **POST** /agreements/{agreementId}/wait | Waits for Agreement approval by the Provider.


# **cancel_agreement**
> cancel_agreement(agreement_id)

Cancels agreement.

Causes the awaiting `waitForApproval` call to return with `Cancelled` response. 

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    agreement_id = 'agreement_id_example' # str | 

    try:
        # Cancels agreement.
        api_instance.cancel_agreement(agreement_id)
    except ApiException as e:
        print("Exception when calling RequestorApi->cancel_agreement: %s\n" % e)
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
**204** | Agreement cancelled. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**409** | Agreement already approved. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **collect_offers**
> list[OneOfProposalEventPropertyQueryEvent] collect_offers(subscription_id, timeout=timeout, max_events=max_events)

Reads Market responses to published Demand.

This is a blocking operation. It will not return until there is at least one new event.  **Note**: When `collectOffers` is waiting, simultaneous call to `unsubscribeDemand` on the same `subscriptionId` should result in \"Subscription does not exist\" error returned from `collectOffers`.  **Note**: Specification requires this endpoint to support list of specific Proposal Ids to listen for messages related only to specific Proposals. This is not covered yet. 

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
timeout = 3.4 # float | How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  (optional)
max_events = 56 # int | Maximum number of events that server should return at once (empty value means no limit).  (optional)

    try:
        # Reads Market responses to published Demand.
        api_response = api_instance.collect_offers(subscription_id, timeout=timeout, max_events=max_events)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->collect_offers: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 
 **timeout** | **float**| How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  | [optional] 
 **max_events** | **int**| Maximum number of events that server should return at once (empty value means no limit).  | [optional] 

### Return type

[**list[OneOfProposalEventPropertyQueryEvent]**](OneOfProposalEventPropertyQueryEvent.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json4, application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Proposal event list. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **confirm_agreement**
> confirm_agreement(agreement_id)

Sends Agreement draft to the Provider.

Signs Agreement self-created via `createAgreement` and sends it to the Provider. 

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    agreement_id = 'agreement_id_example' # str | 

    try:
        # Sends Agreement draft to the Provider.
        api_instance.confirm_agreement(agreement_id)
    except ApiException as e:
        print("Exception when calling RequestorApi->confirm_agreement: %s\n" % e)
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
**204** | Agreement confirmed. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**410** | Agreement cancelled. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **counter_proposal_demand**
> str counter_proposal_demand(subscription_id, proposal_id, proposal)

Responds with a bespoke Demand to received Offer.

Creates and sends a modified version of original Demand (a counter-proposal) adjusted to previously received Proposal (ie. Offer). Changes Proposal state to `Draft`. Returns created Proposal id. 

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
proposal_id = 'proposal_id_example' # str | 
proposal = openapi_market_client.Proposal() # Proposal | 

    try:
        # Responds with a bespoke Demand to received Offer.
        api_response = api_instance.counter_proposal_demand(subscription_id, proposal_id, proposal)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->counter_proposal_demand: %s\n" % e)
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

# **create_agreement**
> str create_agreement(agreement_proposal)

Creates Agreement from selected Proposal.

Initiates the Agreement handshake phase.  Formulates an Agreement artifact from the Proposal indicated by the received Proposal Id.  The Approval Expiry Date is added to Agreement artifact and implies the effective timeout on the whole Agreement Confirmation sequence.  A successful call to `createAgreement` shall immediately be followed by a `confirmAgreement` and `waitForApproval` call in order to listen for responses from the Provider.  **Note**: Moves given Proposal to `Approved` state. 

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    agreement_proposal = openapi_market_client.AgreementProposal() # AgreementProposal | 

    try:
        # Creates Agreement from selected Proposal.
        api_response = api_instance.create_agreement(agreement_proposal)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->create_agreement: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agreement_proposal** | [**AgreementProposal**](AgreementProposal.md)|  | 

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
**201** | Agreement created. |  -  |
**400** | Bad request. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
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
    api_instance = openapi_market_client.RequestorApi(api_client)
    agreement_id = 'agreement_id_example' # str | 

    try:
        # Fetches agreement with given agreement id.
        api_response = api_instance.get_agreement(agreement_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_agreement: %s\n" % e)
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

# **get_demands**
> list[OneOfDemand] get_demands()

Fetches all active Demands which have been published by the Requestor.

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    
    try:
        # Fetches all active Demands which have been published by the Requestor.
        api_response = api_instance.get_demands()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_demands: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[OneOfDemand]**](OneOfDemand.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Demand list. |  -  |
**400** | Bad request. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_proposal_offer**
> Proposal get_proposal_offer(subscription_id, proposal_id)

Fetches Proposal (Offer) with given id.

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
proposal_id = 'proposal_id_example' # str | 

    try:
        # Fetches Proposal (Offer) with given id.
        api_response = api_instance.get_proposal_offer(subscription_id, proposal_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_proposal_offer: %s\n" % e)
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

# **post_query_reply_demands**
> post_query_reply_demands(subscription_id, query_id, body)

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
query_id = 'query_id_example' # str | 
body = None # object | 

    try:
        # Handles dynamic property query.
        api_instance.post_query_reply_demands(subscription_id, query_id, body)
    except ApiException as e:
        print("Exception when calling RequestorApi->post_query_reply_demands: %s\n" % e)
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

# **reject_proposal_offer**
> reject_proposal_offer(subscription_id, proposal_id)

Rejects Proposal (Offer).

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
proposal_id = 'proposal_id_example' # str | 

    try:
        # Rejects Proposal (Offer).
        api_instance.reject_proposal_offer(subscription_id, proposal_id)
    except ApiException as e:
        print("Exception when calling RequestorApi->reject_proposal_offer: %s\n" % e)
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

# **subscribe_demand**
> str subscribe_demand(demand)

Publishes Requestor capabilities via Demand.

Demand object can be considered an \"open\" or public Demand, as it is not directed at a specific Provider, but rather is sent to the market so that the matching mechanism implementation can associate relevant Offers.  **Note**: it is an \"atomic\" operation, ie. as soon as Subscription is placed, the Demand is published on the market. 

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    demand = openapi_market_client.Demand() # Demand | 

    try:
        # Publishes Requestor capabilities via Demand.
        api_response = api_instance.subscribe_demand(demand)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->subscribe_demand: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **demand** | [**Demand**](Demand.md)|  | 

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    agreement_id = 'agreement_id_example' # str | 

    try:
        # Terminates approved Agreement.
        api_instance.terminate_agreement(agreement_id)
    except ApiException as e:
        print("Exception when calling RequestorApi->terminate_agreement: %s\n" % e)
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

# **unsubscribe_demand**
> unsubscribe_demand(subscription_id)

Stop subscription for previously published Demand.

Stop receiving Proposals.  **Note**: this will terminate all pending `collectOffers` calls on this subscription. This implies, that client code should not `unsubscribeDemand` before it has received all expected/useful inputs from `collectOffers`. 

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    subscription_id = 'subscription_id_example' # str | 

    try:
        # Stop subscription for previously published Demand.
        api_instance.unsubscribe_demand(subscription_id)
    except ApiException as e:
        print("Exception when calling RequestorApi->unsubscribe_demand: %s\n" % e)
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
**204** | Demand revoked. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**410** | Already unsubscribed. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **wait_for_approval**
> str wait_for_approval(agreement_id, timeout=timeout)

Waits for Agreement approval by the Provider.

This is a blocking operation. The call may be aborted by Requestor caller code. After the call is aborted, another `waitForApproval` call can be raised on the same Agreement Id.  It returns one of the following options: * `Ok` - Indicates that the Agreement has been approved by the Provider.   - The Provider is now ready to accept a request to start an Activity     as described in the negotiated agreement.   - The Requestor’s corresponding `waitForApproval` call returns Ok after     this on the Provider side.  * `Rejected` - Indicates that the Provider has called `rejectAgreement`,   which effectively stops the Agreement handshake. The Requestor may attempt   to return to the Negotiation phase by sending a new Proposal.  * `Cancelled` - Indicates that the Requestor himself has called  `cancelAgreement`, which effectively stops the Agreement handshake. 

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
    api_instance = openapi_market_client.RequestorApi(api_client)
    agreement_id = 'agreement_id_example' # str | 
timeout = 3.4 # float | How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  (optional)

    try:
        # Waits for Agreement approval by the Provider.
        api_response = api_instance.wait_for_approval(agreement_id, timeout=timeout)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->wait_for_approval: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agreement_id** | **str**|  | 
 **timeout** | **float**| How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  | [optional] 

### Return type

**str**

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Agreement approval result. |  -  |
**401** | Authorization information is missing or invalid. |  -  |
**404** | The specified resource was not found. |  -  |
**0** | Unexpected error. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

