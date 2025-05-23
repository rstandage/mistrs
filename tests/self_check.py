from mistrs import get_credentials, get_headers, get

credentials = get_credentials()
headers = get_headers(credentials["api_token"])
url = f'{credentials["api_url"]}self'
data = get(url, headers)