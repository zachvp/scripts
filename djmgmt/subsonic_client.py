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
import xml.etree.ElementTree as ET
import keyring

def create_token(password: str, salt: str) -> str:
    return hashlib.md5((password + salt).encode()).hexdigest()

def create_salt(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# construct query params
password = keyring.get_password('navidrome_client', 'api_client')
assert password, f'unable to fetch password'
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
# dbg = {
#     'url': response.url,
#     'status_code': response.status_code,
#     'text': response.text
# }
# print(json.dumps(dbg, indent=2))

response_content = ET.fromstring(response.text).attrib
if response.status_code == 200:
    print(f'successful call to {endpoint}')
    if endpoint == 'ping':
        status = response_content['status']
        print(f'status: {status}')
        
else:
    '''
    0 	A generic error.
    10 	Required parameter is missing.
    20 	Incompatible Subsonic REST protocol version. Client must upgrade.
    30 	Incompatible Subsonic REST protocol version. Server must upgrade.
    40 	Wrong username or password.
    41 	Token authentication not supported for LDAP users.
    50 	User is not authorized for the given operation.
    60 	The trial period for the Subsonic server is over. Please upgrade to Subsonic Premium. Visit subsonic.org for details.
    70 	The requested data was not found.
    '''
    print(f'error: {response.text}')

