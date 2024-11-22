'''
Subsonic client
Primary functionality
    * startScan
    * report when scan is finished
'''

'''
Request steps
    URL encode request params
    
'''

from urllib.parse import urlencode
import requests
import hashlib
import random
import string
import json

def create_token(password: str, salt: str) -> str:
    return hashlib.md5((password + salt).encode()).hexdigest()

def create_salt(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# construct query params
password = ''
salt = create_salt(12)
base_params = {
    'u': 'api_client',                      # user
    't': f'{create_token(password, salt)}', # token
    's': f'{salt}',                         # salt
    'v': '1.16.1',                          # version
    'c': 'corevega_client'                  # client id
}
query_string = urlencode(base_params)

# call the endpoint
endpoint = 'ping'
base_url = f"http://corevega.local:4533/rest"
url = f"{base_url}/{endpoint}.view?{query_string}"
print(f'send request: {url}')
response = requests.get(url)

# handle the response
response = {
    'url': response.url,
    'status_code': response.status_code,
    'text': response.text
}
print(json.dumps(response, indent=2))

