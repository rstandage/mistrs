
# mistrs v0.1.8

**mistrs** is a Python library designed to simplify interactions with the Mist API. It provides tools for API interaction, authentication, and data handling, making it easier to manage Mist programmatically.

---

## Features

- **Authentication Management**: Easily manage credentials for different Mist environments.
- **API Interaction**: Simplified functions for GET, PUT and POST requests to the Mist API.
- **Pagination Handling**: Automatically handle paginated API responses.
- **Data Handling**: Read, modify and create XLSX/CSV files for readable data output
- **Error Checking** Create and map graphs to analyse issues
---

## Installation

To install the library, use pip:

```bash
pip install mistrs 
```

## Quick Start

### Authentication Setup

The library supports multiple Mist environments (e.g., `global01`, `emea01`) and securely stores your credentials in .mistrs in your home directory

```python

from mistrs import get_credentials, get_headers

# Interactive mode - will prompt for environment selection and API token
credentials = get_credentials()

# Non-interactive mode with specific environment
credentials = get_credentials(environment="emea01", interactive=False)

#get_headers will create the headers for API calls.
headers = get_headers(credentials["api_token"])


```

To handle org level tokens, you can add the one-time-token arg into get_credentials. This will also provide the option to save the file

```python
from mistrs import get_credentials
credentials = get_credentials()

```


### Making API requests

The library supports all API functions, get, post, put and delete.

```python

from mistrs import get_credentials, get_headers, get, post

# Get credentials
credentials = get_credentials()

# Set up headers with authentication
headers = get_headers(credentials["api_token"])

#Create org sites url
url = f"{credentials['api_url']}orgs/{org_id}/sites"

#Get data from API
sites = get(url, headers)

#Create a new site
new_site = {
    "country_code": "GB",
    "timezone": "Europe/London",
    "sitegroup_ids": [],
    "notes": "",
    "latlng": {
        "lat": 51.630336,
        "lng": -0.799728
    },
    "name": "Brand New Site",
    "rftemplate_id": None,
    "aptemplate_id": None,
    "secpolicy_id": None,
    "alarmtemplate_id": None,
    "networktemplate_id": None,
    "gatewaytemplate_id": None,
    "sitetemplate_id": None
}
response, data = post(new_site, url, headers)
if response:
    print(f"Created site with ID: {data.get('id')}")

```

### Handling Paginated Responses
There is a specific function to support endpoints with large datasets that require pagination

```python

from mistrs import get_credentials, get_headers, get_paginated

# Get credentials
credentials = get_credentials()

# Set up headers with authentication
headers = get_headers(credentials["api_token"])

#Create org sites url
url = f"{credentials['api_url']}orgs/{org_id}/devices"

#Get all devices
all_aps = get_paginated(url, headers, limit=100, show_progress=True, debug=False)
```
### Handling data

The library had functions for handling data, for example this is how we can create an Excel file for our APs

```python
from mistrs import create_xlsx

#Create file path
filepath = 'my_aps.xlsx'

#create file
create_xlsx(all_aps, filepath)
#

```

### Tracking Errors

This function takes error data collected from Mist and creates graphs to easily analyze the data
```python

from mistrs import get_credentials, get_headers, get_paginated, analyze_errors

# Get credentials
credentials = get_credentials(environment="emea02")

# Set up headers with authentication
headers = get_headers(credentials["api_token"])

# Get errors
org_id = '3b2fc535-8266-4974-9f68-e55db37cf85f'
error = 'AP_DISCONNECTED'
url = f"{credentials['api_url']}orgs/{org_id}/devices/events/search?type={error}&duration=7d"
data = get_paginated(url, headers, limit=100, show_progress=True)
processed_data = analyze_errors(
    data=data,
    site_array=Site_Array, #Optional to convert id to name
    error=error,
    group_by='site',
    top_n=10,
    save_path=f'top_{top_n}_{error}.png'
)
```


### Licenses
This project is licensed under the MIT license