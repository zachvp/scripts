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
from requests import Response
import requests
import hashlib
import random
import string
import json
import xml.etree.ElementTree as ET
import keyring
import argparse

def parse_args(valid_endpoints: set[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('endpoint', type=str, help=f"Which endpoint to call. One of: '{valid_endpoints}'")
    
    args = parser.parse_args()
    
    if args.endpoint not in valid_endpoints:
        parser.error(f"invalid function: '{args.function}")
    
    return args

def create_token(password: str, salt: str) -> str:
    return hashlib.md5((password + salt).encode()).hexdigest()

def create_salt(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_query_string():
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
    return urlencode(base_params)

def call_endpoint(endpoint: str) -> Response:
    # call the endpoint
    query_string = create_query_string()
    base_url = f"http://corevega.local:4533/rest"
    url = f"{base_url}/{endpoint}.view?{query_string}"
    print(f'send request: {url}')
    return requests.get(url)

def get_response_content(response: Response):
    return ET.fromstring(response.text).attrib

if __name__ == '__main__':
    script_args = parse_args({'ping', 'startScan', 'scanStatus'})
    response = call_endpoint(script_args.endpoint)
    response_content = get_response_content(response)
    
    if response.status_code == 200:
        print(f'successful call to {script_args.endpoint}')
        if script_args.endpoint == 'ping':
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

