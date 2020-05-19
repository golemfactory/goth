# openapi_activity_client.RequestorStateApi

All URIs are relative to *http://localhost/activity-api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_activity_state**](RequestorStateApi.md#get_activity_state) | **GET** /activity/{activityId}/state | Get state of specified Activity.
[**get_activity_usage**](RequestorStateApi.md#get_activity_usage) | **GET** /activity/{activityId}/usage | Get usage of specified Activity.
[**get_running_command**](RequestorStateApi.md#get_running_command) | **GET** /activity/{activityId}/command | Get running command for a specified Activity.


# **get_activity_state**
> ActivityState get_activity_state(activity_id)

Get state of specified Activity.

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
    api_instance = openapi_activity_client.RequestorStateApi(api_client)
    activity_id = 'activity_id_example' # str | 

    try:
        # Get state of specified Activity.
        api_response = api_instance.get_activity_state(activity_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorStateApi->get_activity_state: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **activity_id** | **str**|  | 

### Return type

[**ActivityState**](ActivityState.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | Not Found |  -  |
**500** | Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_activity_usage**
> list[float] get_activity_usage(activity_id)

Get usage of specified Activity.

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
    api_instance = openapi_activity_client.RequestorStateApi(api_client)
    activity_id = 'activity_id_example' # str | 

    try:
        # Get usage of specified Activity.
        api_response = api_instance.get_activity_usage(activity_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorStateApi->get_activity_usage: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **activity_id** | **str**|  | 

### Return type

**list[float]**

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | Not Found |  -  |
**500** | Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_running_command**
> ExeScriptCommandState get_running_command(activity_id)

Get running command for a specified Activity.

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
    api_instance = openapi_activity_client.RequestorStateApi(api_client)
    activity_id = 'activity_id_example' # str | 

    try:
        # Get running command for a specified Activity.
        api_response = api_instance.get_running_command(activity_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RequestorStateApi->get_running_command: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **activity_id** | **str**|  | 

### Return type

[**ExeScriptCommandState**](ExeScriptCommandState.md)

### Authorization

[app_key](../README.md#app_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | Not Found |  -  |
**500** | Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

