import requests, json, time, urllib.parse, re
from tqdm import tqdm


def _debug(debug, message):
    if debug:
        print(f"[DEBUG] {message}")


def post(data, url, headers, debug=False):
    """POST data to Mist API.

    Args:
        data (dict): Payload to send
        url (str): Full API endpoint URL
        headers (dict): Request headers (from get_headers or credentials['headers'])
        debug (bool): Print request/response details

    Returns:
        tuple: (success: bool, response: dict)
    """
    _debug(debug, f"POST {url}")
    _debug(debug, f"Payload: {json.dumps(data, indent=2)}")
    try:
        send = requests.post(url, json=data, headers=headers)
        _debug(debug, f"Status: {send.status_code}")
        text = send.json() if send.text else {}
        if send.status_code in (200, 201):
            print('Done')
            return True, text
        else:
            print(f"Failed - HTTP Error {send.status_code}")
            _debug(debug, f"Response: {send.text}")
            return False, text
    except Exception as e:
        print(f"POST request failed: {e}")
        return False, {}


def put(data, url, headers, debug=False):
    """PUT data to Mist API.

    Args:
        data (dict): Payload to send
        url (str): Full API endpoint URL
        headers (dict): Request headers (from get_headers or credentials['headers'])
        debug (bool): Print request/response details

    Returns:
        tuple: (success: bool, response: dict)
    """
    _debug(debug, f"PUT {url}")
    _debug(debug, f"Payload: {json.dumps(data, indent=2)}")
    try:
        send = requests.put(url, json=data, headers=headers)
        _debug(debug, f"Status: {send.status_code}")
        text = send.json() if send.text else {}
        if send.status_code in (200, 201, 204):
            print('Done')
            return True, text
        else:
            print(f"Failed - HTTP Error {send.status_code}")
            _debug(debug, f"Response: {send.text}")
            return False, text
    except Exception as e:
        print(f"PUT request failed: {e}")
        return False, {}


def delete(url, headers, debug=False):
    """DELETE a resource from Mist API.

    Args:
        url (str): Full API endpoint URL
        headers (dict): Request headers (from get_headers or credentials['headers'])
        debug (bool): Print request/response details

    Returns:
        tuple: (success: bool, response_text: str)
    """
    _debug(debug, f"DELETE {url}")
    try:
        response = requests.delete(url, headers=headers)
        _debug(debug, f"Status: {response.status_code}")
        if response.status_code in (200, 204):
            return True, response.text
        else:
            print(f"Failed - HTTP Error {response.status_code}: {response.text}")
            return False, response.text
    except requests.exceptions.RequestException as e:
        print(f"DELETE request failed: {e}")
        return False, str(e)


def get(url, headers, debug=False):
    """GET data from Mist API.

    Args:
        url (str): Full API endpoint URL
        headers (dict): Request headers (from get_headers or credentials['headers'])
        debug (bool): Print request/response details

    Returns:
        dict | list | None: Parsed JSON response, or None on error
    """
    _debug(debug, f"GET {url}")
    try:
        resp = requests.get(url, headers=headers)
        _debug(debug, f"Status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        print(f"GET request failed: {e}")
        return None


def get_paginated(initial_url, headers, limit=100, show_progress=True, debug=False):
    """Fetch all pages from a paginated Mist API endpoint.

    Handles two pagination styles:
      - Dict responses with a 'results' field (standard search endpoints)
      - List responses with page-based pagination (e.g. /stats/devices)

    Uses X-Page-Total / X-Page-Page / X-Page-Limit headers for progress tracking.

    Args:
        initial_url (str): Starting URL (query params will be added/appended)
        headers (dict): Request headers (from get_headers or credentials['headers'])
        limit (int): Items per page (default: 100)
        show_progress (bool): Show tqdm progress bar (default: True)
        debug (bool): Print pagination debug info (default: False)

    Returns:
        list: All items combined across all pages
    """
    parsed_url = urllib.parse.urlparse(initial_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    _debug(debug, f"Base URL: {base_url}")

    if '?' in initial_url:
        if 'limit=' not in initial_url:
            initial_url += f'&limit={limit}'
    else:
        initial_url += f'?limit={limit}'

    _debug(debug, f"Initial URL: {initial_url}")

    all_items = []
    current_url = initial_url
    pbar = None
    total_items = None
    pagination_type = None

    _debug(debug, f"Making initial request to {current_url}")
    response = requests.get(current_url, headers=headers)
    _debug(debug, f"Status: {response.status_code}")

    if response.status_code != 200:
        _debug(debug, f"Response: {response.text}")
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")

    header_total = response.headers.get("X-Page-Total")
    if header_total is not None:
        try:
            total_items = int(header_total)
            _debug(debug, f"Total from header: {total_items}")
        except (ValueError, TypeError):
            pass

    data = response.json()

    if isinstance(data, dict) and 'results' in data:
        pagination_type = 'results'
        _debug(debug, "Detected standard 'results' pagination")

        all_items = data['results'].copy()
        _debug(debug, f"First page: {len(all_items)} items")

        if total_items is None:
            total_items = data.get('total')

        if show_progress:
            pbar = tqdm(total=total_items, desc="Fetching data") if total_items else tqdm(desc="Fetching data")
            pbar.update(len(data['results']))

        next_path = data.get('next')
        next_url = None
        if next_path:
            next_url = f"{base_url}{next_path}" if next_path.startswith('/') else next_path
            _debug(debug, f"Next URL: {next_url}")

        page = 1

        while True:
            if next_url:
                current_url = next_url
            else:
                if total_items is not None and len(all_items) >= total_items:
                    _debug(debug, f"Reached total: {len(all_items)}/{total_items}")
                    break
                page += 1
                if 'page=' in current_url:
                    current_url = re.sub(r'page=\d+', f'page={page}', current_url)
                elif '?' in current_url:
                    current_url = f"{current_url}&page={page}"
                else:
                    current_url = f"{current_url}?page={page}"

            _debug(debug, f"Fetching: {current_url}")
            response = requests.get(current_url, headers=headers)
            _debug(debug, f"Status: {response.status_code}")

            if response.status_code != 200:
                if pbar:
                    pbar.close()
                break

            data = response.json()

            if isinstance(data, dict) and 'results' in data:
                page_items = data['results']
                _debug(debug, f"Page items: {len(page_items)}")
                if not page_items:
                    break
                all_items.extend(page_items)
                if pbar:
                    pbar.update(len(page_items))

                next_path = data.get('next')
                next_url = None
                if next_path:
                    next_url = f"{base_url}{next_path}" if next_path.startswith('/') else next_path
                    _debug(debug, f"Next URL: {next_url}")
            else:
                break

            time.sleep(0.1)

    elif isinstance(data, list):
        pagination_type = 'list'
        _debug(debug, f"Detected list response: {len(data)} items")
        all_items = data.copy()

        page_header = response.headers.get("X-Page-Page")
        limit_header = response.headers.get("X-Page-Limit")

        current_page = 1
        if page_header:
            try:
                current_page = int(page_header)
            except (ValueError, TypeError):
                pass

        page_limit = limit
        if limit_header:
            try:
                page_limit = int(limit_header)
            except (ValueError, TypeError):
                pass

        if show_progress:
            pbar = tqdm(total=total_items, desc="Fetching pages") if total_items else tqdm(desc="Fetching pages")
            pbar.update(len(data))

        while len(data) == page_limit:
            current_page += 1
            _debug(debug, f"Fetching page {current_page}")

            if 'page=' in current_url:
                next_url = re.sub(r'page=\d+', f'page={current_page}', current_url)
            elif '?' in current_url:
                next_url = f"{current_url}&page={current_page}"
            else:
                next_url = f"{current_url}?page={current_page}"

            response = requests.get(next_url, headers=headers)
            _debug(debug, f"Status: {response.status_code}")

            if response.status_code != 200:
                if pbar:
                    pbar.close()
                break

            data = response.json()

            if not isinstance(data, list):
                break

            _debug(debug, f"Page {current_page}: {len(data)} items")
            all_items.extend(data)
            if pbar:
                pbar.update(len(data))

            if total_items is not None and len(all_items) >= total_items:
                break

            time.sleep(0.1)

    else:
        pagination_type = 'unknown'
        _debug(debug, f"Unknown pagination type: {type(data)}")
        all_items = data

    if pbar:
        pbar.close()

    print(f"Pagination type: {pagination_type} | Total items retrieved: {len(all_items) if isinstance(all_items, list) else 'N/A'}")
    return all_items
