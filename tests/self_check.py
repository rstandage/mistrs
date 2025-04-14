from mistrs.auth import get_credentials, get_headers
from mistrs.api import get
from mistrs.data import pprint

credentials = get_credentials()
headers = get_headers(credentials["api_token"])
url = f'{credentials["api_url"]}/self'
data = get(url, headers)
pprint(data)