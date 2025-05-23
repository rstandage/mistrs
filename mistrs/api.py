import requests, json, time, urllib.parse
from tqdm import tqdm



def post(data, url, headers):
#POST data to mist. input requires (data, url, headers)
    payload = json.dumps(data)
    send = requests.request("POST", url, data=payload, headers=headers)
    text = json.loads(send.text)
    if send.status_code == 200:
        response = True
        print ('Done')
    else:
        print("Failed - HTTP Error {}".format(send.status_code))
        response = False
    return response, text
 
def put(data, url, headers):
#PUT data to mist. input requires (data, url, headers)
    payload = json.dumps(data)
    send = requests.request("PUT", url, data=payload, headers=headers)
    text = json.loads(send.text)
    if send.status_code == 200:
        response = True
        print ('Done')
    else:
        print("Failed - HTTP Error {}".format(send.status_code))
        response = False
    return response, text

def delete(url, headers):
    # DELETE data from mist. URL requires full endpoint to remove. Input requires (url, headers)
    try:
        response = requests.request("DELETE", url, headers=headers)
        if response.status_code == 200:
            return True, response.text
        else:
            print(f"Failed - HTTP Error {response.status_code}: {response.text}")
            return False, response.text
    except requests.exceptions.RequestException as e:
        return False, print(f"Request failed: {str(e)}")

def get(url, headers):
    # GET data from mist. input requires (url, headers). return will be an array of the response
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()  # Check for HTTP errors
        data = json.loads(resp.text)
        return data
    except Exception as e:
        print(f"Error in API request: {e}")
        return None

import requests
import time
from tqdm import tqdm
import urllib.parse
import re

def get_paginated(initial_url, headers, limit=100, show_progress=True, debug=False):
    """
    Get all paginated results from the MIST API, supporting both:
    1. Dict responses with 'results' field (standard pagination)
    2. List responses that support page parameter (like /stats/devices)

    Uses HTTP headers (X-Page-Total, X-Page-Page, X-Page-Limit) for progress tracking when available.

    Args:
        initial_url (str): The initial URL to query
        headers (dict): Headers to include in the request
        limit (int): Number of items per page (default: 100)
        show_progress (bool): Whether to show a progress bar (default: True)
        debug (bool): Whether to print debug information (default: False)

    Returns:
        list: All items from the paginated API
    """
    def debug_print(message):
        if debug:
            print(f"DEBUG: {message}")

    # Extract base URL (scheme + netloc) for handling relative URLs
    parsed_url = urllib.parse.urlparse(initial_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    debug_print(f"Base URL: {base_url}")

    # Add limit parameter to URL if not already present
    if '?' in initial_url:
        if 'limit=' not in initial_url:
            initial_url += f'&limit={limit}'
    else:
        initial_url += f'?limit={limit}'

    debug_print(f"Initial URL: {initial_url}")

    all_items = []
    current_url = initial_url
    pbar = None
    total_items = None
    pagination_type = None

    # Make initial request
    debug_print(f"Making initial request to {current_url}")
    response = requests.get(current_url, headers=headers)

    debug_print(f"Response status code: {response.status_code}")
    if response.status_code != 200:
        debug_print(f"Response text: {response.text}")
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    # Try to get total from headers
    header_total = response.headers.get("X-Page-Total")
    if header_total is not None:
        try:
            total_items = int(header_total)
            debug_print(f"Total items from header: {total_items}")
        except (ValueError, TypeError):
            debug_print(f"Could not parse X-Page-Total header: {header_total}")

    data = response.json()

    # Determine response type and pagination strategy
    if isinstance(data, dict) and 'results' in data:
        # This is standard pagination with results field
        pagination_type = 'results'
        debug_print(f"Detected standard pagination with 'results' field")
        debug_print(f"Response keys: {list(data.keys())}")

        # Initialize all_items with first page results
        all_items = data['results'].copy()  # Use copy() to avoid reference issues
        debug_print(f"Added {len(data['results'])} items from first page")

        # Get total if available from response or use header total
        if total_items is None:
            total_items = data.get('total', None)
            if total_items is not None:
                debug_print(f"Total expected from response: {total_items}")

        # Setup progress bar if requested
        if show_progress:
            if total_items is not None:
                pbar = tqdm(total=total_items, desc="Fetching data")
            else:
                pbar = tqdm(desc="Fetching data")
            pbar.update(len(data['results']))

        # Check if we have a 'next' field for pagination
        next_path = data.get('next')
        next_url = None
        if next_path:
            # Handle relative URLs by prepending the base URL
            if next_path.startswith('/'):
                next_url = f"{base_url}{next_path}"
            else:
                next_url = next_path
            debug_print(f"Next URL (from response): {next_url}")

        # If no 'next' field but we have 'total', use page-based pagination
        page = 1

        # Continue fetching pages until we have all items or no more pages
        while True:
            if next_url:
                # Use the 'next' URL provided by the API
                debug_print(f"Using next URL: {next_url}")
                current_url = next_url
            else:
                # If no 'next' URL but we know there are more items, construct page URL
                if total_items is not None and len(all_items) >= total_items:
                    debug_print(f"Reached total items ({len(all_items)} of {total_items})")
                    break

                page += 1
                debug_print(f"Constructing URL for page {page}")

                # Construct URL with page parameter
                if 'page=' in current_url:
                    current_url = re.sub(r'page=\d+', f'page={page}', current_url)
                else:
                    if '?' in current_url:
                        current_url = f"{current_url}&page={page}"
                    else:
                        current_url = f"{current_url}?page={page}"

            debug_print(f"Next request URL: {current_url}")

            # Make request for next page
            response = requests.get(current_url, headers=headers)
            debug_print(f"Response status code: {response.status_code}")

            if response.status_code != 200:
                debug_print(f"Response text: {response.text}")
                if pbar is not None:
                    pbar.close()
                # Don't raise exception, just stop paginating
                break

            data = response.json()

            # Check if we got a valid response with results
            if isinstance(data, dict) and 'results' in data:
                page_items = data['results']
                debug_print(f"Page has {len(page_items)} items")

                if not page_items:  # Empty results, we're done
                    debug_print("Empty results, stopping pagination")
                    break

                all_items.extend(page_items)
                if pbar is not None:
                    pbar.update(len(page_items))

                # Update next_url for next iteration
                next_path = data.get('next')
                next_url = None
                if next_path:
                    # Handle relative URLs by prepending the base URL
                    if next_path.startswith('/'):
                        next_url = f"{base_url}{next_path}"
                    else:
                        next_url = next_path
                    debug_print(f"Next URL from response: {next_url}")
                else:
                    debug_print("No next URL in response")

                debug_print(f"Total items so far: {len(all_items)}")
            else:
                debug_print(f"No 'results' key in response, stopping pagination")
                break

            # Avoid rate limiting
            time.sleep(0.1)

    elif isinstance(data, list):
        # This is a list response that might support page-based pagination
        pagination_type = 'list'
        debug_print(f"Detected list response with {len(data)} items")
        all_items = data.copy()  # Use copy() to avoid reference issues

        # Get pagination info from headers
        page_header = response.headers.get("X-Page-Page")
        limit_header = response.headers.get("X-Page-Limit")

        current_page = 1
        if page_header:
            try:
                current_page = int(page_header)
                debug_print(f"Current page from header: {current_page}")
            except (ValueError, TypeError):
                debug_print(f"Could not parse X-Page-Page header: {page_header}")

        page_limit = limit
        if limit_header:
            try:
                page_limit = int(limit_header)
                debug_print(f"Page limit from header: {page_limit}")
            except (ValueError, TypeError):
                debug_print(f"Could not parse X-Page-Limit header: {limit_header}")

        # Setup progress bar if requested
        if show_progress:
            if total_items is not None:
                pbar = tqdm(total=total_items, desc="Fetching pages (list endpoint)")
                pbar.update(len(data))
            else:
                pbar = tqdm(desc="Fetching pages (list endpoint)")
                pbar.update(len(data))

        # Continue fetching pages until we get an empty list or fewer items than limit
        while len(data) == page_limit:
            current_page += 1
            debug_print(f"Fetching page {current_page} for list response")

            # Construct URL with page parameter
            if 'page=' in current_url:
                next_url = re.sub(r'page=\d+', f'page={current_page}', current_url)
            else:
                if '?' in current_url:
                    next_url = f"{current_url}&page={current_page}"
                else:
                    next_url = f"{current_url}?page={current_page}"

            debug_print(f"Next URL: {next_url}")

            # Make request for next page
            response = requests.get(next_url, headers=headers)
            debug_print(f"Response status code: {response.status_code}")

            if response.status_code != 200:
                debug_print(f"Response text: {response.text}")
                if pbar is not None:
                    pbar.close()
                break  # Don't raise exception, just stop paginating

            # Check headers again for updated pagination info
            page_header = response.headers.get("X-Page-Page")
            if page_header:
                try:
                    current_page = int(page_header)
                    debug_print(f"Current page from header: {current_page}")
                except (ValueError, TypeError):
                    pass

            data = response.json()

            if not isinstance(data, list):
                debug_print(f"Response is not a list, stopping pagination")
                break

            debug_print(f"Page {current_page} has {len(data)} items")
            all_items.extend(data)

            if pbar is not None:
                pbar.update(len(data))

            # Check if we've reached the total
            if total_items is not None and len(all_items) >= total_items:
                debug_print(f"Reached total items ({len(all_items)} of {total_items})")
                break

            # Avoid rate limiting
            time.sleep(0.1)

    else:
        # Unknown pagination type or no pagination
        pagination_type = 'unknown'
        debug_print(f"Unknown pagination type or no pagination")
        debug_print(f"Response type: {type(data)}")
        if isinstance(data, dict):
            debug_print(f"Response keys: {list(data.keys())}")
        all_items = data

    if pbar is not None:
        pbar.close()

    print(f"Pagination type detected: {pagination_type}")
    print(f"Total items retrieved: {len(all_items) if isinstance(all_items, list) else 'N/A (not a list)'}")

    return all_items