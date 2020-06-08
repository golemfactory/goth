# openapi_activity_client.ProviderApi

All URIs are relative to *http://localhost/activity-api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**collect_activity_events**](ProviderApi.md#collect_activity_events) | **GET** /events | Fetch Requestor command events.
[**get_activity_state**](ProviderApi.md#get_activity_state) | **GET** /activity/{activityId}/state | Get state of specified Activity.
[**get_activity_usage**](ProviderApi.md#get_activity_usage) | **GET** /activity/{activityId}/usage | Get usage of specified Activity.
[**set_activity_state**](ProviderApi.md#set_activity_state) | **PUT** /activity/{activityId}/state | Set state of specified Activity.


# **collect_activity_events**
> list[OneOfCreateActivityDestroyActivityGetActivityStateGetActivityUsage] collect_activity_events(timeout=timeout, max_events=max_events)

Fetch Requestor command events.

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
    api_instance = openapi_activity_client.ProviderApi(api_client)
    timeout = 3.4 # float | How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  (optional)
max_events = 56 # int | Maximum number of events that server should return at once (empty value means no limit).  (optional)

    try:
        # Fetch Requestor command events.
        api_response = api_instance.collect_activity_events(timeout=timeout, max_events=max_events)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->collect_activity_events: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **timeout** | **float**| How many seconds server should wait for new events (0.0 means it should return immediately if there are no events)  | [optional] 
 **max_events** | **int**| Maximum number of events that server should return at once (empty value means no limit).  | [optional] 

### Return type

[**list[OneOfCreateActivityDestroyActivityGetActivityStateGetActivityUsage]**](OneOfCreateActivityDestroyActivityGetActivityStateGetActivityUsage.md)

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
**500** | Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

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
    api_instance = openapi_activity_client.ProviderApi(api_client)
    activity_id = 'activity_id_example' # str | 

    try:
        # Get state of specified Activity.
        api_response = api_instance.get_activity_state(activity_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_activity_state: %s\n" % e)
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
    api_instance = openapi_activity_client.ProviderApi(api_client)
    activity_id = 'activity_id_example' # str | 

    try:
        # Get usage of specified Activity.
        api_response = api_instance.get_activity_usage(activity_id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling ProviderApi->get_activity_usage: %s\n" % e)
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

# **set_activity_state**
> set_activity_state(activity_id, activity_state)

Set state of specified Activity.

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
    api_instance = openapi_activity_client.ProviderApi(api_client)
    activity_id = 'activity_id_example' # str | 
activity_state = openapi_activity_client.ActivityState() # ActivityState | 

    try:
        # Set state of specified Activity.
        api_instance.set_activity_state(activity_id, activity_state)
    except ApiException as e:
        print("Exception when calling ProviderApi->set_activity_state: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **activity_id** | **str**|  | 
 **activity_state** | [**ActivityState**](ActivityState.md)|  | 

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
**200** | Success |  -  |
**404** | Not Found |  -  |
**500** | Server Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

