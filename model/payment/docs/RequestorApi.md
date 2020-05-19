# openapi_payment_client.RequestorApi

All URIs are relative to *http://localhost/payment-api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**accept_debit_note**](RequestorApi.md#accept_debit_note) | **POST** /requestor/debitNotes/{debitNodeId}/accept | Accept received Debit Note.
[**accept_invoice**](RequestorApi.md#accept_invoice) | **POST** /requestor/invoices/{invoiceId}/accept | Accept received Invoice.
[**amend_allocation**](RequestorApi.md#amend_allocation) | **PUT** /requestor/allocations/{allocationId} | Amend Allocation.
[**create_allocation**](RequestorApi.md#create_allocation) | **POST** /requestor/allocations | Create Allocation.
[**get_allocation**](RequestorApi.md#get_allocation) | **GET** /requestor/allocations/{allocationId} | Get Allocation.
[**get_allocations**](RequestorApi.md#get_allocations) | **GET** /requestor/allocations | Get Allocations.
[**get_outgoing_payment**](RequestorApi.md#get_outgoing_payment) | **GET** /requestor/payments/{paymentId} | Get outgoing Payment.
[**get_outgoing_payments**](RequestorApi.md#get_outgoing_payments) | **GET** /requestor/payments | Get outgoing Payments.
[**get_payments_for_received_debit_note**](RequestorApi.md#get_payments_for_received_debit_note) | **GET** /requestor/debitNotes/{debitNodeId}/payments | Get Payments for Debit Note.
[**get_payments_for_received_invoice**](RequestorApi.md#get_payments_for_received_invoice) | **GET** /requestor/invoices/{invoiceId}/payments | Get Payments for received Invoice.
[**get_received_debit_note**](RequestorApi.md#get_received_debit_note) | **GET** /requestor/debitNotes/{debitNodeId} | Get Debit Note.
[**get_received_debit_notes**](RequestorApi.md#get_received_debit_notes) | **GET** /requestor/debitNotes | Get Debit Notes received by this Requestor.
[**get_received_invoice**](RequestorApi.md#get_received_invoice) | **GET** /requestor/invoices/{invoiceId} | Get Invoice.
[**get_received_invoices**](RequestorApi.md#get_received_invoices) | **GET** /requestor/invoices | Get Invoices received by this Requestor.
[**get_requestor_debit_note_events**](RequestorApi.md#get_requestor_debit_note_events) | **GET** /requestor/debitNoteEvents | Get Debit Note events.
[**get_requestor_invoice_events**](RequestorApi.md#get_requestor_invoice_events) | **GET** /requestor/invoiceEvents | Get Invoice events.
[**reject_debit_note**](RequestorApi.md#reject_debit_note) | **POST** /requestor/debitNotes/{debitNodeId}/reject | Reject received Debit Note.
[**reject_invoice**](RequestorApi.md#reject_invoice) | **POST** /requestor/invoices/{invoiceId}/reject | Reject received Invoice.
[**release_allocation**](RequestorApi.md#release_allocation) | **DELETE** /requestor/allocations/{allocationId} | Release Allocation.


# **accept_debit_note**
> accept_debit_note(debit_node_id, acceptance, timeout=timeout)

Accept received Debit Note.

Send Debit Note Accepted message to Debit Note Issuer. Trigger payment orchestration for this Debit Note (using allocated lot identified by AllocationId if any).  This is a blocking operation. It will not return until the Requestor has acknowledged accepting the Invoice or timeout has passed.  NOTE: An Accepted Debit Note cannot be Rejected later. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    debit_node_id = 'debit_node_id_example' # str | 
acceptance = openapi_payment_client.Acceptance() # Acceptance | 
timeout = 60 # float | How many seconds server should wait for acknowledgement from the remote party (0 means forever)  (optional) (default to 60)

    try:
        # Accept received Debit Note.
        api_instance.accept_debit_note(debit_node_id, acceptance, timeout=timeout)
    except ApiException as e:
        print("Exception when calling RequestorApi->accept_debit_note: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **debit_node_id** | **str**|  | 
 **acceptance** | [**Acceptance**](Acceptance.md)|  | 
 **timeout** | **float**| How many seconds server should wait for acknowledgement from the remote party (0 means forever)  | [optional] [default to 60]

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
**200** | OK |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |
**504** | The Requestor has not responded to the request within timeout. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **accept_invoice**
> accept_invoice(invoice_id, acceptance, timeout=timeout)

Accept received Invoice.

Send Invoice Accepted message to Invoice Issuer. Trigger payment orchestration for this Invoice (using allocated lot identified by AllocationId if any).  This is a blocking operation. It will not return until the Requestor has acknowledged rejecting the Invoice or timeout has passed.  NOTE: An Accepted Invoice cannot be Rejected later. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    invoice_id = 'invoice_id_example' # str | 
acceptance = openapi_payment_client.Acceptance() # Acceptance | 
timeout = 60 # float | How many seconds server should wait for acknowledgement from the remote party (0 means forever)  (optional) (default to 60)

    try:
        # Accept received Invoice.
        api_instance.accept_invoice(invoice_id, acceptance, timeout=timeout)
    except ApiException as e:
        print("Exception when calling RequestorApi->accept_invoice: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **invoice_id** | **str**|  | 
 **acceptance** | [**Acceptance**](Acceptance.md)|  | 
 **timeout** | **float**| How many seconds server should wait for acknowledgement from the remote party (0 means forever)  | [optional] [default to 60]

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
**200** | OK |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |
**504** | The Requestor has not responded to the request within timeout. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **amend_allocation**
> Allocation amend_allocation(allocation_id, allocation)

Amend Allocation.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    allocation_id = 'allocation_id_example' # str | 
allocation = openapi_payment_client.Allocation() # Allocation | 

    try:
        # Amend Allocation.
        api_response = api_instance.amend_allocation(allocation_id, allocation)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->amend_allocation: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **allocation_id** | **str**|  | 
 **allocation** | [**Allocation**](Allocation.md)|  | 

### Return type

[**Allocation**](Allocation.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_allocation**
> Allocation create_allocation(allocation)

Create Allocation.

Allocate funds to make sure they are not spent elsewhere.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    allocation = openapi_payment_client.Allocation() # Allocation | 

    try:
        # Create Allocation.
        api_response = api_instance.create_allocation(allocation)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->create_allocation: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **allocation** | [**Allocation**](Allocation.md)|  | 

### Return type

[**Allocation**](Allocation.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | OK |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_allocation**
> Allocation get_allocation(allocation_id)

Get Allocation.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    allocation_id = 'allocation_id_example' # str | 

    try:
        # Get Allocation.
        api_response = api_instance.get_allocation(allocation_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_allocation: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **allocation_id** | **str**|  | 

### Return type

[**Allocation**](Allocation.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_allocations**
> list[Allocation] get_allocations()

Get Allocations.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    
    try:
        # Get Allocations.
        api_response = api_instance.get_allocations()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_allocations: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[Allocation]**](Allocation.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_outgoing_payment**
> Allocation get_outgoing_payment(payment_id)

Get outgoing Payment.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    payment_id = 'payment_id_example' # str | 

    try:
        # Get outgoing Payment.
        api_response = api_instance.get_outgoing_payment(payment_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_outgoing_payment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **payment_id** | **str**|  | 

### Return type

[**Allocation**](Allocation.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_outgoing_payments**
> list[Payment] get_outgoing_payments(timeout=timeout, later_than=later_than)

Get outgoing Payments.

Payments can be treated as events and this method can be used to listen for new payments by long-polling.  If there are any payments the method will return them immediately. If there are none the method will wait until one appears or timeout passes. `laterThan` parameter can be used in order to get just the 'new' payments. Setting the parameter value to the timestamp of the last processed payment ensures that no payments will go unnoticed. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    timeout = 0 # float | How many seconds server should wait for new events (0 means it should return immediately if there are no events)  (optional) (default to 0)
later_than = '2013-10-20T19:20:30+01:00' # datetime | Show only events later than specified timeout (optional)

    try:
        # Get outgoing Payments.
        api_response = api_instance.get_outgoing_payments(timeout=timeout, later_than=later_than)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_outgoing_payments: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **timeout** | **float**| How many seconds server should wait for new events (0 means it should return immediately if there are no events)  | [optional] [default to 0]
 **later_than** | **datetime**| Show only events later than specified timeout | [optional] 

### Return type

[**list[Payment]**](Payment.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_payments_for_received_debit_note**
> list[Payment] get_payments_for_received_debit_note(debit_node_id)

Get Payments for Debit Note.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    debit_node_id = 'debit_node_id_example' # str | 

    try:
        # Get Payments for Debit Note.
        api_response = api_instance.get_payments_for_received_debit_note(debit_node_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_payments_for_received_debit_note: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **debit_node_id** | **str**|  | 

### Return type

[**list[Payment]**](Payment.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_payments_for_received_invoice**
> list[Payment] get_payments_for_received_invoice(invoice_id)

Get Payments for received Invoice.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    invoice_id = 'invoice_id_example' # str | 

    try:
        # Get Payments for received Invoice.
        api_response = api_instance.get_payments_for_received_invoice(invoice_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_payments_for_received_invoice: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **invoice_id** | **str**|  | 

### Return type

[**list[Payment]**](Payment.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_received_debit_note**
> DebitNote get_received_debit_note(debit_node_id)

Get Debit Note.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    debit_node_id = 'debit_node_id_example' # str | 

    try:
        # Get Debit Note.
        api_response = api_instance.get_received_debit_note(debit_node_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_received_debit_note: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **debit_node_id** | **str**|  | 

### Return type

[**DebitNote**](DebitNote.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_received_debit_notes**
> list[DebitNote] get_received_debit_notes()

Get Debit Notes received by this Requestor.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    
    try:
        # Get Debit Notes received by this Requestor.
        api_response = api_instance.get_received_debit_notes()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_received_debit_notes: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[DebitNote]**](DebitNote.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_received_invoice**
> Invoice get_received_invoice(invoice_id)

Get Invoice.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    invoice_id = 'invoice_id_example' # str | 

    try:
        # Get Invoice.
        api_response = api_instance.get_received_invoice(invoice_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_received_invoice: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **invoice_id** | **str**|  | 

### Return type

[**Invoice**](Invoice.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_received_invoices**
> list[Invoice] get_received_invoices()

Get Invoices received by this Requestor.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    
    try:
        # Get Invoices received by this Requestor.
        api_response = api_instance.get_received_invoices()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_received_invoices: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[Invoice]**](Invoice.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_requestor_debit_note_events**
> list[DebitNoteEvent] get_requestor_debit_note_events(timeout=timeout, later_than=later_than)

Get Debit Note events.

Listen for Debit Note-related events using long-polling. If there are any events the method will return them immediately. If there are none the method will wait until one appears or timeout passes. `laterThan` parameter can be used in order to get just the 'new' events. Setting the parameter value to the timestamp of the last processed event ensures that no events will go unnoticed. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    timeout = 0 # float | How many seconds server should wait for new events (0 means it should return immediately if there are no events)  (optional) (default to 0)
later_than = '2013-10-20T19:20:30+01:00' # datetime | Show only events later than specified timeout (optional)

    try:
        # Get Debit Note events.
        api_response = api_instance.get_requestor_debit_note_events(timeout=timeout, later_than=later_than)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_requestor_debit_note_events: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **timeout** | **float**| How many seconds server should wait for new events (0 means it should return immediately if there are no events)  | [optional] [default to 0]
 **later_than** | **datetime**| Show only events later than specified timeout | [optional] 

### Return type

[**list[DebitNoteEvent]**](DebitNoteEvent.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_requestor_invoice_events**
> list[InvoiceEvent] get_requestor_invoice_events(timeout=timeout, later_than=later_than)

Get Invoice events.

Listen for Invoice-related events using long-polling. If there are any events the method will return them immediately. If there are none the method will wait until one appears or timeout passes. `laterThan` parameter can be used in order to get just the 'new' events. Setting the parameter value to the timestamp of the last processed event ensures that no events will go unnoticed. 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    timeout = 0 # float | How many seconds server should wait for new events (0 means it should return immediately if there are no events)  (optional) (default to 0)
later_than = '2013-10-20T19:20:30+01:00' # datetime | Show only events later than specified timeout (optional)

    try:
        # Get Invoice events.
        api_response = api_instance.get_requestor_invoice_events(timeout=timeout, later_than=later_than)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorApi->get_requestor_invoice_events: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **timeout** | **float**| How many seconds server should wait for new events (0 means it should return immediately if there are no events)  | [optional] [default to 0]
 **later_than** | **datetime**| Show only events later than specified timeout | [optional] 

### Return type

[**list[InvoiceEvent]**](InvoiceEvent.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reject_debit_note**
> reject_debit_note(debit_node_id, rejection, timeout=timeout)

Reject received Debit Note.

Send Debit Note Rejected message to Invoice Issuer. Notification of rejection is signalling that Requestor does not accept the Debit Note (for some reason).  This is a blocking operation. It will not return until the Requestor has acknowledged rejecting the Invoice or timeout has passed.  NOTE: A Rejected Debit Note can be Accepted subsequently (e.g. as a result of some arbitrage). 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    debit_node_id = 'debit_node_id_example' # str | 
rejection = openapi_payment_client.Rejection() # Rejection | 
timeout = 60 # float | How many seconds server should wait for acknowledgement from the remote party (0 means forever)  (optional) (default to 60)

    try:
        # Reject received Debit Note.
        api_instance.reject_debit_note(debit_node_id, rejection, timeout=timeout)
    except ApiException as e:
        print("Exception when calling RequestorApi->reject_debit_note: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **debit_node_id** | **str**|  | 
 **rejection** | [**Rejection**](Rejection.md)|  | 
 **timeout** | **float**| How many seconds server should wait for acknowledgement from the remote party (0 means forever)  | [optional] [default to 60]

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
**200** | OK |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |
**504** | The Requestor has not responded to the request within timeout. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reject_invoice**
> reject_invoice(invoice_id, rejection, timeout=timeout)

Reject received Invoice.

Send Invoice Rejected message to Invoice Issuer. Notification of rejection is signalling that Requestor does not accept Invoice (for some reason).  This is a blocking operation. It will not return until the Requestor has acknowledged rejecting the Invoice or timeout has passed.  NOTE: A Rejected Invoice can be Accepted subsequently (e.g. as a result of some arbitrage). 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    invoice_id = 'invoice_id_example' # str | 
rejection = openapi_payment_client.Rejection() # Rejection | 
timeout = 60 # float | How many seconds server should wait for acknowledgement from the remote party (0 means forever)  (optional) (default to 60)

    try:
        # Reject received Invoice.
        api_instance.reject_invoice(invoice_id, rejection, timeout=timeout)
    except ApiException as e:
        print("Exception when calling RequestorApi->reject_invoice: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **invoice_id** | **str**|  | 
 **rejection** | [**Rejection**](Rejection.md)|  | 
 **timeout** | **float**| How many seconds server should wait for acknowledgement from the remote party (0 means forever)  | [optional] [default to 60]

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
**200** | OK |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |
**504** | The Requestor has not responded to the request within timeout. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **release_allocation**
> release_allocation(allocation_id)

Release Allocation.

The Allocation of amount is released. Note that this operation releases currently allocated amount (which may have been reduced by subsequent Invoice Payments).  If the Allocation was connected with a Deposit the release amount from Deposit shall be marked as pending to be paid back to Requestor - and eventually will be paid back, unless a subsequent Allocation with Deposit is made. The Payment Platform implementations may optimize unnecessary fund transfers (i.e. will not pay back the Deposit if released funds can be assigned to a new Allocation with Deposit). 

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_payment_client
from openapi_payment_client.rest import ApiException
from pprint import pprint
configuration = openapi_payment_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/payment-api/v1
configuration.host = "http://localhost/payment-api/v1"

# Enter a context with an instance of the API client
with openapi_payment_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_payment_client.RequestorApi(api_client)
    allocation_id = 'allocation_id_example' # str | 

    try:
        # Release Allocation.
        api_instance.release_allocation(allocation_id)
    except ApiException as e:
        print("Exception when calling RequestorApi->release_allocation: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **allocation_id** | **str**|  | 

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
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**404** | Object not found |  -  |
**500** | Server error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

