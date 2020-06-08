# openapi_payment_client.ProviderApi

All URIs are relative to *http://localhost/payment-api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**cancel_debit_note**](ProviderApi.md#cancel_debit_note) | **POST** /provider/debitNotes/{debitNodeId}/cancel | Cancel Debit Note.
[**cancel_invoice**](ProviderApi.md#cancel_invoice) | **POST** /provider/invoices/{invoiceId}/cancel | Cancel Invoice.
[**get_incoming_payment**](ProviderApi.md#get_incoming_payment) | **GET** /provider/payments/{paymentId} | Get incoming Payment.
[**get_incoming_payments**](ProviderApi.md#get_incoming_payments) | **GET** /provider/payments | Get incoming Payments.
[**get_issued_debit_note**](ProviderApi.md#get_issued_debit_note) | **GET** /provider/debitNotes/{debitNodeId} | Get Debit Note.
[**get_issued_debit_notes**](ProviderApi.md#get_issued_debit_notes) | **GET** /provider/debitNotes | Get Debit Notes issued by this Provider.
[**get_issued_invoice**](ProviderApi.md#get_issued_invoice) | **GET** /provider/invoices/{invoiceId} | Get Invoice.
[**get_issued_invoices**](ProviderApi.md#get_issued_invoices) | **GET** /provider/invoices | Get Invoices issued by this Provider.
[**get_payments_for_issued_debit_note**](ProviderApi.md#get_payments_for_issued_debit_note) | **GET** /provider/debitNotes/{debitNodeId}/payments | Get Payments for Debit Note.
[**get_payments_for_issued_invoice**](ProviderApi.md#get_payments_for_issued_invoice) | **GET** /provider/invoices/{invoiceId}/payments | Get Payments for issued Invoice.
[**get_provider_debit_note_events**](ProviderApi.md#get_provider_debit_note_events) | **GET** /provider/debitNoteEvents | Get Debit Note events.
[**get_provider_invoice_events**](ProviderApi.md#get_provider_invoice_events) | **GET** /provider/invoiceEvents | Get Invoice events.
[**issue_debit_note**](ProviderApi.md#issue_debit_note) | **POST** /provider/debitNotes | Issue a Debit Note.
[**issue_invoice**](ProviderApi.md#issue_invoice) | **POST** /provider/invoices | Issue an Invoice.
[**send_debit_note**](ProviderApi.md#send_debit_note) | **POST** /provider/debitNotes/{debitNodeId}/send | Send Debit Note to Requestor.
[**send_invoice**](ProviderApi.md#send_invoice) | **POST** /provider/invoices/{invoiceId}/send | Send Invoice to Requestor.


# **cancel_debit_note**
> cancel_debit_note(debit_node_id, timeout=timeout)

Cancel Debit Note.

This is a blocking operation. It will not return until the Requestor has acknowledged cancelling the Debit Note or timeout has passed. The Requestor may refuse to cancel the Debit Note if they have already paid it. 

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    debit_node_id = 'debit_node_id_example' # str | 
timeout = 60 # float | How many seconds server should wait for acknowledgement from the remote party (0 means forever)  (optional) (default to 60)

    try:
        # Cancel Debit Note.
        api_instance.cancel_debit_note(debit_node_id, timeout=timeout)
    except ApiException as e:
        print("Exception when calling ProviderApi->cancel_debit_note: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **debit_node_id** | **str**|  | 
 **timeout** | **float**| How many seconds server should wait for acknowledgement from the remote party (0 means forever)  | [optional] [default to 60]

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
**409** | The Requestor has refused to cancel the Debit Note. |  -  |
**500** | Server error |  -  |
**504** | The Requestor has not responded to the request within timeout. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **cancel_invoice**
> cancel_invoice(invoice_id, timeout=timeout)

Cancel Invoice.

This is a blocking operation. It will not return until the Requestor has acknowledged cancelling the Invoice or timeout has passed. The Requestor may refuse to cancel the Invoice if they have already paid it. 

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    invoice_id = 'invoice_id_example' # str | 
timeout = 60 # float | How many seconds server should wait for acknowledgement from the remote party (0 means forever)  (optional) (default to 60)

    try:
        # Cancel Invoice.
        api_instance.cancel_invoice(invoice_id, timeout=timeout)
    except ApiException as e:
        print("Exception when calling ProviderApi->cancel_invoice: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **invoice_id** | **str**|  | 
 **timeout** | **float**| How many seconds server should wait for acknowledgement from the remote party (0 means forever)  | [optional] [default to 60]

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
**409** | The Requestor has refused to cancel the Invoice. |  -  |
**500** | Server error |  -  |
**504** | The Requestor has not responded to the request within timeout. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_incoming_payment**
> Allocation get_incoming_payment(payment_id)

Get incoming Payment.

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    payment_id = 'payment_id_example' # str | 

    try:
        # Get incoming Payment.
        api_response = api_instance.get_incoming_payment(payment_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_incoming_payment: %s\n" % e)
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

# **get_incoming_payments**
> list[Payment] get_incoming_payments(timeout=timeout, later_than=later_than)

Get incoming Payments.

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    timeout = 0 # float | How many seconds server should wait for new events (0 means it should return immediately if there are no events)  (optional) (default to 0)
later_than = '2013-10-20T19:20:30+01:00' # datetime | Show only events later than specified timeout (optional)

    try:
        # Get incoming Payments.
        api_response = api_instance.get_incoming_payments(timeout=timeout, later_than=later_than)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_incoming_payments: %s\n" % e)
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

# **get_issued_debit_note**
> DebitNote get_issued_debit_note(debit_node_id)

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    debit_node_id = 'debit_node_id_example' # str | 

    try:
        # Get Debit Note.
        api_response = api_instance.get_issued_debit_note(debit_node_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_issued_debit_note: %s\n" % e)
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

# **get_issued_debit_notes**
> list[DebitNote] get_issued_debit_notes()

Get Debit Notes issued by this Provider.

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    
    try:
        # Get Debit Notes issued by this Provider.
        api_response = api_instance.get_issued_debit_notes()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_issued_debit_notes: %s\n" % e)
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

# **get_issued_invoice**
> Invoice get_issued_invoice(invoice_id)

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    invoice_id = 'invoice_id_example' # str | 

    try:
        # Get Invoice.
        api_response = api_instance.get_issued_invoice(invoice_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_issued_invoice: %s\n" % e)
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

# **get_issued_invoices**
> list[Invoice] get_issued_invoices()

Get Invoices issued by this Provider.

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    
    try:
        # Get Invoices issued by this Provider.
        api_response = api_instance.get_issued_invoices()
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_issued_invoices: %s\n" % e)
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

# **get_payments_for_issued_debit_note**
> list[Payment] get_payments_for_issued_debit_note(debit_node_id)

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    debit_node_id = 'debit_node_id_example' # str | 

    try:
        # Get Payments for Debit Note.
        api_response = api_instance.get_payments_for_issued_debit_note(debit_node_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_payments_for_issued_debit_note: %s\n" % e)
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

# **get_payments_for_issued_invoice**
> list[Payment] get_payments_for_issued_invoice(invoice_id)

Get Payments for issued Invoice.

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    invoice_id = 'invoice_id_example' # str | 

    try:
        # Get Payments for issued Invoice.
        api_response = api_instance.get_payments_for_issued_invoice(invoice_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_payments_for_issued_invoice: %s\n" % e)
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

# **get_provider_debit_note_events**
> list[InvoiceEvent] get_provider_debit_note_events(timeout=timeout, later_than=later_than)

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    timeout = 0 # float | How many seconds server should wait for new events (0 means it should return immediately if there are no events)  (optional) (default to 0)
later_than = '2013-10-20T19:20:30+01:00' # datetime | Show only events later than specified timeout (optional)

    try:
        # Get Debit Note events.
        api_response = api_instance.get_provider_debit_note_events(timeout=timeout, later_than=later_than)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_provider_debit_note_events: %s\n" % e)
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

# **get_provider_invoice_events**
> list[InvoiceEvent] get_provider_invoice_events(timeout=timeout, later_than=later_than)

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    timeout = 0 # float | How many seconds server should wait for new events (0 means it should return immediately if there are no events)  (optional) (default to 0)
later_than = '2013-10-20T19:20:30+01:00' # datetime | Show only events later than specified timeout (optional)

    try:
        # Get Invoice events.
        api_response = api_instance.get_provider_invoice_events(timeout=timeout, later_than=later_than)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_provider_invoice_events: %s\n" % e)
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

# **issue_debit_note**
> DebitNote issue_debit_note(debit_note)

Issue a Debit Note.

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    debit_note = openapi_payment_client.DebitNote() # DebitNote | 

    try:
        # Issue a Debit Note.
        api_response = api_instance.issue_debit_note(debit_note)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->issue_debit_note: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **debit_note** | [**DebitNote**](DebitNote.md)|  | 

### Return type

[**DebitNote**](DebitNote.md)

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

# **issue_invoice**
> Invoice issue_invoice(invoice)

Issue an Invoice.

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    invoice = openapi_payment_client.Invoice() # Invoice | 

    try:
        # Issue an Invoice.
        api_response = api_instance.issue_invoice(invoice)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->issue_invoice: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **invoice** | [**Invoice**](Invoice.md)|  | 

### Return type

[**Invoice**](Invoice.md)

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

# **send_debit_note**
> send_debit_note(debit_node_id, timeout=timeout)

Send Debit Note to Requestor.

This is a blocking operation. It will not return until the Requestor has acknowledged receiving the Debit Note or timeout has passed. 

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    debit_node_id = 'debit_node_id_example' # str | 
timeout = 60 # float | How many seconds server should wait for acknowledgement from the remote party (0 means forever)  (optional) (default to 60)

    try:
        # Send Debit Note to Requestor.
        api_instance.send_debit_note(debit_node_id, timeout=timeout)
    except ApiException as e:
        print("Exception when calling ProviderApi->send_debit_note: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **debit_node_id** | **str**|  | 
 **timeout** | **float**| How many seconds server should wait for acknowledgement from the remote party (0 means forever)  | [optional] [default to 60]

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
**504** | The Requestor has not responded to the request within timeout. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **send_invoice**
> send_invoice(invoice_id, timeout=timeout)

Send Invoice to Requestor.

This is a blocking operation. It will not return until the Requestor has acknowledged receiving the Invoice or timeout has passed. 

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
    api_instance = openapi_payment_client.ProviderApi(api_client)
    invoice_id = 'invoice_id_example' # str | 
timeout = 60 # float | How many seconds server should wait for acknowledgement from the remote party (0 means forever)  (optional) (default to 60)

    try:
        # Send Invoice to Requestor.
        api_instance.send_invoice(invoice_id, timeout=timeout)
    except ApiException as e:
        print("Exception when calling ProviderApi->send_invoice: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **invoice_id** | **str**|  | 
 **timeout** | **float**| How many seconds server should wait for acknowledgement from the remote party (0 means forever)  | [optional] [default to 60]

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
**504** | The Requestor has not responded to the request within timeout. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

