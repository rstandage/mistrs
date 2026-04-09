# mistrs v0.2.0 — LLM Script Reference

**mistrs** is a Python library for interacting with the Juniper Mist Cloud API.
It handles authentication, HTTP operations, pagination, and data export.

---

## Canonical Script Pattern

Every script follows this structure. Copy it as your starting point.

```python
from dataclasses import dataclass, field
from pathlib import Path
from mistrs import get_credentials, get, get_paginated, post, put, delete, create_csv, create_xlsx

@dataclass
class APIConfig:
    api_url: str
    headers: dict
    org_id: str
    org_name: str
    limit: int = 100
    debug: bool = False
    output_dir: Path = field(default_factory=lambda: Path.home() / "created_files")

def main():
    creds = get_credentials()          # interactive, org token flow
    config = APIConfig(
        api_url=creds['api_url'],
        headers=creds['headers'],      # pre-built — no separate get_headers() call needed
        org_id=creds['org_id'],
        org_name=creds['org_name'],
    )
    config.output_dir.mkdir(exist_ok=True)

    # Build URLs from config
    url = f"{config.api_url}orgs/{config.org_id}/devices/search?type=ap"
    devices = get_paginated(url, config.headers, limit=config.limit, debug=config.debug)
    create_csv(devices, config.output_dir / "devices.csv")

if __name__ == "__main__":
    main()
```

---

## Authentication — `auth.py`

### `get_credentials(environment=None, interactive=True, org_token=True, otp=None) → dict`

The entry point for every script. Returns a dict with everything needed to make API calls.

**Return dict keys:**

| Key | Type | Notes |
|-----|------|-------|
| `api_url` | str | Base URL, always trailing slash. Use directly in f-strings. |
| `api_token` | str | Raw token string |
| `headers` | dict | Pre-built headers — use this in all API calls |
| `org_id` | str | Organization UUID (org_token flow only) |
| `org_name` | str | Organization display name (org_token flow only) |
| `environment` | str | e.g. `'emea01'`, `'global01'` |
| `created` | str | ISO timestamp when token was stored |

**When called interactively** (default): presents a menu of stored tokens or option to enter a new one. Tokens are stored in `~/.mistrs/` as JSON files.

**When called non-interactively**: loads a previously stored token for the given environment. Raises `ValueError` if none exists.

```python
# Standard interactive (recommended)
creds = get_credentials()

# Non-interactive (e.g. in a scheduled script)
creds = get_credentials(environment='emea01', interactive=False)

# Regular token (not org-scoped)
creds = get_credentials(org_token=False)
```

### `get_headers(token: str) → dict`

Builds `{'Content-Type': 'application/json', 'Authorization': 'Token <token>'}`.
You don't need this if you use `creds['headers']`, but it's available standalone.

### `validate_credentials(api_url, api_token) → dict`

Calls `/self` and returns user/org data. Raises `ValueError` on failure.

---

## API Operations — `api.py`

All functions accept `headers` (the dict from `creds['headers']`) and an optional `debug=True` flag that prints `[DEBUG]` lines showing URLs, status codes, and payloads.

### `get(url, headers, debug=False) → dict | list | None`

Simple GET. Returns parsed JSON or `None` on error.

```python
sites = get(f"{config.api_url}orgs/{config.org_id}/sites", config.headers)
```

### `get_paginated(initial_url, headers, limit=100, show_progress=True, debug=False) → list`

Fetches all pages automatically. Handles both pagination styles:
- **Dict with `results`** — standard search endpoints (`/search`, `/events/search`, etc.)
- **List response** — stats endpoints like `/stats/devices`

Uses `X-Page-Total` / `X-Page-Page` / `X-Page-Limit` response headers for progress tracking.
Shows a `tqdm` progress bar by default.

```python
# Search endpoint (returns dict with 'results')
clients = get_paginated(
    f"{config.api_url}orgs/{config.org_id}/clients/search?duration=7d",
    config.headers,
    limit=200,
    debug=config.debug
)

# Stats endpoint (returns list)
device_stats = get_paginated(
    f"{config.api_url}orgs/{config.org_id}/stats/devices?type=ap",
    config.headers
)
```

### `post(data, url, headers, debug=False) → (bool, dict)`

POST JSON body. Returns `(True, response_dict)` on HTTP 200/201, `(False, response_dict)` otherwise.

```python
payload = {"name": "New Site", "country_code": "GB", "timezone": "Europe/London"}
success, resp = post(payload, f"{config.api_url}orgs/{config.org_id}/sites", config.headers)
if success:
    site_id = resp['id']
```

### `put(data, url, headers, debug=False) → (bool, dict)`

PUT JSON body. Returns `(True, response_dict)` on HTTP 200/201/204, `(False, response_dict)` otherwise.
Handles empty response bodies (204 No Content) without error.

```python
update = {"enabled": True, "vlan_id": 100}
success, resp = put(update, f"{config.api_url}sites/{site_id}/setting", config.headers)
```

### `delete(url, headers, debug=False) → (bool, str)`

DELETE a resource. Returns `(True, response_text)` on HTTP 200/204.

```python
success, _ = delete(f"{config.api_url}sites/{site_id}/devices/{device_id}", config.headers)
```

---

## Data Utilities — `data.py`

### File I/O

```python
from mistrs import create_csv, create_xlsx, read_csv, read_xlsx

create_csv(data, "output.csv")           # list of dicts → CSV
create_xlsx(data, "output.xlsx")         # list of dicts → Excel
rows = read_csv("input.csv")             # CSV → list of dicts
rows = read_xlsx("input.xlsx")           # Excel → list of dicts
```

### Formatting helpers

```python
from mistrs import jprint, print_table, clean_mac, edittime, list_ids, analyze_errors

jprint(data)                             # pretty-print JSON to stdout
print(print_table(data))                 # PrettyTable from list of dicts
print(print_table(data, headers=["A","B"]))  # custom column headers

clean_mac("aa:bb:cc:dd:ee:ff")           # → 'aabbccddeeff'
clean_mac("aabb.ccdd.eeff")              # → 'aabbccddeeff'

edittime(1683936000)                     # → '2023-05-13 00:00:00'

ids = list_ids(sites)                    # → ['uuid1', 'uuid2', ...]
```

### `analyze_errors(data, site_array=None, error='Error', group_by='site', top_n=None, save_path=None)`

Plots event data as a time-series chart grouped by site or AP.

```python
events = get_paginated(
    f"{config.api_url}orgs/{config.org_id}/devices/events/search?type=AP_DISCONNECTED&duration=7d",
    config.headers
)
analyze_errors(events, group_by='site', top_n=10, save_path='disconnections.png')
```

---

## Network Utilities — `net.py`

### `subnet(network: str, cidr: int) → list`

Splits a supernet into smaller subnets.

```python
from mistrs import subnet   # if exported, else: from mistrs.net import subnet

subnets = subnet("10.0.0.0/8", 24)
# Returns list of dicts: [{'Seq':1, 'Network':'10.0.0.0/24', 'First Host':..., ...}, ...]
```

---

## URL Patterns — Mist API Reference

Build all URLs as `f"{config.api_url}<path>"`. The `api_url` already includes the trailing slash.

```python
# Org-level
f"{config.api_url}orgs/{config.org_id}/sites"
f"{config.api_url}orgs/{config.org_id}/devices/search?type=ap"
f"{config.api_url}orgs/{config.org_id}/clients/search?duration=7d"
f"{config.api_url}orgs/{config.org_id}/devices/events/search?type=AP_DISCONNECTED&duration=7d"
f"{config.api_url}orgs/{config.org_id}/stats"
f"{config.api_url}orgs/{config.org_id}/licenses"

# Site-level
f"{config.api_url}sites/{site_id}/devices"
f"{config.api_url}sites/{site_id}/stats/devices?type=ap"
f"{config.api_url}sites/{site_id}/clients/search"
f"{config.api_url}sites/{site_id}/wlans"
f"{config.api_url}sites/{site_id}/setting"
```

---

## Common Patterns

### Get org_id when it's missing from credentials

```python
def ensure_org_id(creds: dict) -> str:
    org_id = creds.get("org_id")
    if not org_id:
        org_id = input("Enter organization ID: ").strip()
    return org_id
```

### Build a site lookup map

```python
sites = get(f"{config.api_url}orgs/{config.org_id}/sites", config.headers)
site_map = {s['id']: s['name'] for s in sites}
# Usage: site_name = site_map.get(item['site_id'], 'Unknown')
```

### Iterate over all sites and collect data

```python
sites = get(f"{config.api_url}orgs/{config.org_id}/sites", config.headers)
all_data = []
for site in sites:
    url = f"{config.api_url}sites/{site['id']}/clients/search"
    clients = get_paginated(url, config.headers, limit=config.limit)
    for c in clients:
        c['site_name'] = site['name']
    all_data.extend(clients)
```

### Full working script skeleton

```python
from dataclasses import dataclass, field
from pathlib import Path
from datetime import date
import sys
from mistrs import get_credentials, get, get_paginated, post, put, delete, create_csv

@dataclass
class APIConfig:
    api_url: str
    headers: dict
    org_id: str
    org_name: str
    limit: int = 100
    debug: bool = False
    output_dir: Path = field(default_factory=lambda: Path.home() / "created_files")

def main():
    try:
        creds = get_credentials()
        config = APIConfig(
            api_url=creds['api_url'],
            headers=creds['headers'],
            org_id=creds.get('org_id', ''),
            org_name=creds.get('org_name', 'unknown'),
        )
        config.output_dir.mkdir(exist_ok=True)

        # --- your logic here ---
        url = f"{config.api_url}orgs/{config.org_id}/sites"
        sites = get(url, config.headers, debug=config.debug)

        filename = f"{config.org_name.replace(' ', '_')}_sites_{date.today()}.csv"
        create_csv(sites, config.output_dir / filename)
        print(f"Exported {len(sites)} sites.")

    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## Available Environments

| Key | Name | API URL |
|-----|------|---------|
| `global01` | Mist Global 01 | `https://api.mist.com/api/v1/` |
| `global02` | Mist Global 02 | `https://api.gc1.mist.com/api/v1/` |
| `global03` | Mist Global 03 | `https://api.ac2.mist.com/api/v1/` |
| `global04` | Mist Global 04 | `https://api.gc2.mist.com/api/v1/` |
| `global05` | Mist Global 05 | `https://api.gc4.mist.com/api/v1/` |
| `emea01` | Mist EMEA 01 | `https://api.eu.mist.com/api/v1/` |
| `emea02` | Mist EMEA 02 | `https://api.gc3.mist.com/api/v1/` |
| `emea03` | Mist EMEA 03 | `https://api.ac6.mist.com/api/v1/` |
| `apac01` | Mist APAC 01 | `https://api.ac5.mist.com/api/v1/` |

---

## Imports Quick Reference

```python
# All common imports in one line
from mistrs import (
    get_credentials, get_headers,
    get, get_paginated, post, put, delete,
    create_csv, create_xlsx, read_csv, read_xlsx,
    jprint, print_table, clean_mac, edittime, list_ids, analyze_errors
)
```
