# openapi_activity_client.RequestorControlApi

All URIs are relative to *http://localhost/activity-api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**call_exec**](RequestorControlApi.md#call_exec) | **POST** /activity/{activityId}/exec | Executes an ExeScript batch within a given Activity.
[**create_activity**](RequestorControlApi.md#create_activity) | **POST** /activity | Creates new Activity based on given Agreement.
[**destroy_activity**](RequestorControlApi.md#destroy_activity) | **DELETE** /activity/{activityId} | Destroys given Activity.
[**get_exec_batch_results**](RequestorControlApi.md#get_exec_batch_results) | **GET** /activity/{activityId}/exec/{batchId} | Queries for ExeScript batch results.


# **call_exec**
> str call_exec(activity_id, script)

Executes an ExeScript batch within a given Activity.

**Note:** This call shall get routed directly to ExeUnit.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_activity_client
from openapi_activity_client.rest import ApiException
from pprint import pprint
configuration = openapi_activity_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/activity-api/v1
configuration.host = "http://localhost/activity-api/v1"

# Enter a context with an instance of the API client
with openapi_activity_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_activity_client.RequestorControlApi(api_client)
    activity_id = 'activity_id_example' # str | 
script = openapi_activity_client.ExeScriptRequest() # ExeScriptRequest | 

    try:
        # Executes an ExeScript batch within a given Activity.
        api_response = api_instance.call_exec(activity_id, script)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorControlApi->call_exec: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **activity_id** | **str**|  | 
 **script** | [**ExeScriptRequest**](ExeScriptRequest.md)|  | 

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
**200** | Success |  -  |
**400** | Bad Request |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_activity**
> str create_activity(agreement_id)

Creates new Activity based on given Agreement.

**Note:** This call shall get routed as a provider event (see ProviderEvent structure).

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_activity_client
from openapi_activity_client.rest import ApiException
from pprint import pprint
configuration = openapi_activity_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/activity-api/v1
configuration.host = "http://localhost/activity-api/v1"

# Enter a context with an instance of the API client
with openapi_activity_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_activity_client.RequestorControlApi(api_client)
    agreement_id = 'agreement_id_example' # str | 

    try:
        # Creates new Activity based on given Agreement.
        api_response = api_instance.create_activity(agreement_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorControlApi->create_activity: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **agreement_id** | **str**|  | 

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
**201** | Success |  -  |
**400** | Bad Request |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **destroy_activity**
> destroy_activity(activity_id)

Destroys given Activity.

**Note:** This call shall get routed as a provider event (see ProviderEvent structure).

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_activity_client
from openapi_activity_client.rest import ApiException
from pprint import pprint
configuration = openapi_activity_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/activity-api/v1
configuration.host = "http://localhost/activity-api/v1"

# Enter a context with an instance of the API client
with openapi_activity_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_activity_client.RequestorControlApi(api_client)
    activity_id = 'activity_id_example' # str | 

    try:
        # Destroys given Activity.
        api_instance.destroy_activity(activity_id)
    except ApiException as e:
        print("Exception when calling RequestorControlApi->destroy_activity: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **activity_id** | **str**|  | 

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
**200** | Success |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_exec_batch_results**
> list[ExeScriptCommandResult] get_exec_batch_results(activity_id, batch_id, command_index=command_index, timeout=timeout)

Queries for ExeScript batch results.

**Note:** This call shall collect ExeScriptCommand result objects received directly from ExeUnit.

### Example

* Bearer Authentication (app_key):
```python
from __future__ import print_function
import time
import openapi_activity_client
from openapi_activity_client.rest import ApiException
from pprint import pprint
configuration = openapi_activity_client.Configuration()
# Configure Bearer authorization: app_key
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/activity-api/v1
configuration.host = "http://localhost/activity-api/v1"

# Enter a context with an instance of the API client
with openapi_activity_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_activity_client.RequestorControlApi(api_client)
    activity_id = 'activity_id_example' # str | 
batch_id = 'batch_id_example' # str | 
command_index = 3.4 # float | Wait until command with the specified index finishes. Must be accompanied by a valid \"timeout\" query parameter.  (optional)
timeout = 3.4 # float | How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  (optional)

    try:
        # Queries for ExeScript batch results.
        api_response = api_instance.get_exec_batch_results(activity_id, batch_id, command_index=command_index, timeout=timeout)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorControlApi->get_exec_batch_results: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **activity_id** | **str**|  | 
 **batch_id** | **str**|  | 
 **command_index** | **float**| Wait until command with the specified index finishes. Must be accompanied by a valid \&quot;timeout\&quot; query parameter.  | [optional] 
 **timeout** | **float**| How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  | [optional] 

### Return type

[**list[ExeScriptCommandResult]**](ExeScriptCommandResult.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**400** | Bad Request |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**500** | Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

