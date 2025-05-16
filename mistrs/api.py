import requests, json
from urllib.parse import urlparse


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

def get_paginated(initial_url, headers, show_progress=True):
    # GET data from mist when multiple pages are returned. input requires (initial_url, headers). return will be an array of the responses
    all_results = []
    try:
        # Extract base URL from initial URL
        parsed_url = urlparse(initial_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Make initial request
        response = requests.get(initial_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Get total if available
        total_items = data.get('total', 0)
        if show_progress:
            print(f"Fetching data... Total items: {total_items}")
        # Add initial results
        if 'results' in data:
            all_results.extend(data['results'])
            if show_progress:
                print(f"Retrieved {len(all_results)} of {total_items} items")
        # Continue fetching while there's a next page
        while 'next' in data and data['next']:
            next_url = base_url + data['next']
            response = requests.get(next_url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if 'results' in data:
                all_results.extend(data['results'])
                if show_progress:
                    print(f"Retrieved {len(all_results)} of {total_items} items")
        return all_results, True
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {str(e)}")
        return all_results, False
    except (KeyError, ValueError) as e:
        print(f"Data parsing error: {str(e)}")
        return all_results, False


