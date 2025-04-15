# mistrs v0.1.0

**mistrs** is a Python library designed to simplify interactions with the Mist API. It provides tools for API interaction, authentication, and data handling, making it easier to manage Mist programmatically.

---

## Features

- **Authentication Management**: Easily manage credentials for different Mist environments.
- **API Interaction**: Simplified functions for GET, PUT and POST requests to the Mist API.
- **Pagination Handling**: Automatically handle paginated API responses.
- **Data Handling**: Read, modify and create XLSX/CSV files for readable data output

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

from mistrs.auth import get_credentials, get_headers

# Interactive mode - will prompt for environment selection and API token
credentials = get_credentials()

# Non-interactive mode with specific environment
credentials = get_credentials(environment="emea01", interactive=False)

#get_headers will create the headers for API calls. You can also insert an org token here
headers = get_headers(credentials["api_token"])
org_headers = get_headers('ORG_TOKEN_STR')



```

### Making API requests

The library supports all API functions, get, post, put and delete.

```python

from mistrs.auth import get_credentials, get_headers
from mistrs.api import get, post

# Get credentials
credentials = get_credentials(environment="global01")

# Set up headers with authentication
headers = get_headers(credentials["api_token"])

#Create org sites url
url = f"{credentials['api_url']}/orgs/{org_id}/sites"

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
response, data = post(new_site_data, url, headers)
if response:
    print(f"Created site with ID: {data.get('id')}")

```

### Handling Paginated Responses
There is a specific function to support endpoints with large datasets that require pagination

```python

from mistrs.auth import get_credentials, get_headers
from mistrs.api import get, post

# Get credentials
credentials = get_credentials(environment="global01")

# Set up headers with authentication
headers = get_headers(credentials["api_token"])

#Create org sites url
url = f"{credentials['api_url']}/orgs/{org_id}/inventory?type=ap&limit=10"

#Get all devices
all_aps = get_all(url)
```
### Handling data

The library had functions for handling data, for example this is how we can create an Excel file for our APs

```python
from mistrs.data import create_xlsx

#Create file path
filepath = 'my_aps.xlsx'

#create file
create_xlsx(all_aps, filepath)
#

```
### Licenses
This project is licensed under the MIT license