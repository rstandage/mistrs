
# mistrs Library: LLM-Optimized Reference & Best Practices

## Credentials Best Practice (otp=True)

**Always use `get_credentials(otp=True)` as your authentication entry point.** This ensures you are using the most secure and flexible method, supporting org-level one-time tokens and returning all necessary fields for robust script propagation.

### Example Credentials Dataclass

```python
from dataclasses import dataclass

@dataclass
class Credentials:
    api_token: str
    api_url: str
    environment: str
    org_id: str
    org_name: str
```

### Example Usage

```python
from mistrs import get_credentials

raw_creds = get_credentials(otp=True)
creds = Credentials(**raw_creds)
```

- **Always propagate the `creds` object throughout your script for all API calls.**
- **Build URLs and headers using fields from this dataclass.**

---

## Function Reference: All Functions in auth, data, net, and api

### auth.py

- **get_credentials(environment=None, interactive=True, otp=False)**
  - Inputs: environment (str, optional), interactive (bool), otp (bool)
  - Returns: dict with api_token, api_url, created, environment, org_id, org_name

- **get_headers(api_token)**
  - Inputs: api_token (str)
  - Returns: dict with HTTP headers for API calls

- **validate_credentials(api_url: str, api_token: str)**
  - Inputs: API URL and Token from credentials dataclass
  - Outputs: Dict if true with "Key Name", "Organization", "Role", "Org ID"

---

### api.py

- **get(url, headers)**
  - Inputs: url (str), headers (dict)
  - Returns: dict or list (parsed JSON response)

- **post(data, url, headers)**
  - Inputs: data (dict), url (str), headers (dict)
  - Returns: (bool, dict) tuple (success, response data)

- **put(data, url, headers)**
  - Inputs: data (dict), url (str), headers (dict)
  - Returns: (bool, dict) tuple (success, response data)

- **delete(url, headers)**
  - Inputs: url (str), headers (dict)
  - Returns: response object or status

- **get_paginated(url, headers, limit=100, show_progress=True, debug=False)**
  - Inputs: url (str), headers (dict), limit (int), show_progress (bool), debug (bool)
  - Returns: list of all items from paginated endpoint

---

### data.py

- **create_xlsx(data, filepath)**
  - Inputs: data (list of dicts), filepath (str)
  - Returns: None (writes XLSX file)

- **read_xlsx(filepath)**
  - Inputs: filepath (str)
  - Returns: List of items

- **create_csv(data, filepath)**
  - Inputs: data (list of dicts), filepath (str)
  - Returns: None (writes CSV file)

- **read_csv(filepath)**
  - Inputs: filepath (str)
  - Returns: List of items

- **list_ids(data)**
  - Inputs: data
  - Returns: List of IDs for iteration

- **print_table(data, headers=None)**
  - Inputs: json data
  - Outputs: PrettyTable object for printing

- **clean_mac(mac_address: str)**
  - Inputs: MAC address
  - Outputs: normalized mac without colons or periods

- **edittime(epoch_timestamp: str)**
  - Input: epoch string
  - Output: Formatted datetime string in the format 'YYYY-MM-DD HH:MM:SS'
- 

- **analyze_errors(data, site_array=None, error=None, group_by='site', top_n=10, save_path=None)**
  - Inputs: data (list), site_array (optional), error (str, optional), group_by (str), top_n (int), save_path (str, optional)
  - Returns: processed data (and saves plot if save_path is given)

---

### net.py

- **subnet(network: str, cidr: int)**
  - Input: supernet as a string and required smaller ciders as integer
  - Returns: list of smaller subnets

---

## Full Example: LLM-Optimized Script

```python
from dataclasses import dataclass
from mistrs import get_credentials, get_headers, get, post, put, delete, get_paginated, create_xlsx, create_csv, analyze_errors

@dataclass
class Credentials:
    api_token: str
    api_url: str
    created: str
    environment: str
    org_id: str
    org_name: str

# Step 1: Authenticate and propagate credentials
raw_creds = get_credentials(otp=True)
creds = Credentials(**raw_creds)
headers = get_headers(creds.api_token)

# Step 2: Build URLs using creds
org_id = creds.org_id
devices_url = f"{creds.api_url}orgs/{creds.org_id}/devices"

# Step 3: Get all devices (paginated)
devices = get_paginated(devices_url, headers)

# Step 4: Export to Excel and CSV
create_xlsx(devices, "devices.xlsx")
create_csv(devices, "devices.csv")

# Step 5: Analyze errors
error_url = f"{creds.api_url}orgs/{creds.org_id}/devices/events/search?type=AP_DISCONNECTED&duration=7d"
error_data = get_paginated(error_url, headers)
analyze_errors(error_data, group_by="site", top_n=10, save_path="top_10_ap_disconnected.png")
```

---

**For all scripts, always start with `get_credentials(otp=True)` and propagate the resulting dataclass.**
**Scripts should also prompt for input if required, for example search limits and propagate the dataclass**