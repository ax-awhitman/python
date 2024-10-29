import datetime
import pip._vendor.requests as requests
import argparse
import time
import json
import sys
import csv
import os


# --Function Block-- #

# Exit handler (Error)
def ax_exit_error(error_code, error_message=None, system_message=None):
    print(error_code)
    if error_message is not None:
        print(error_message)
    if system_message is not None:
        print(system_message)
    sys.exit(1)


# Execute the API call
def get_zone_policies(ax_api_key, org_id, url, params=None, data=None, try_count=0, max_retries=2):
    retry_statuses = [429, 500, 502, 503, 504]
    retry_wait_timer = 5

    params = {
    "o": f"{org_id}",
    "page": "0",
    "limit": "500"
    }
    
    headers = {
    "Authorization": "Bearer " + ax_api_key
  }
  
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code in retry_statuses:
        try_count = try_count + 1
        if try_count <= max_retries:
            time.sleep(retry_wait_timer)
            return get_zone_policies(ax_api_key=ax_api_key, org_id=org_id, url=url, params=params, try_count=try_count, max_retries=max_retries)
        else:
            if not response:
               print(response.json())
            response.raise_for_status()

    else:
        if not response:
          print(response.json())
        response.raise_for_status()

    api_response_package = {}
    api_response_package['statusCode'] = response.status_code
    try:
        api_response_package['data'] = response.json()
    except ValueError:
        if response.text == '':
            api_response_package['data'] = None
        else:
            ax_exit_error(501, 'The server returned an unexpected server response.')
    return api_response_package
    

# Page wrapper for API Call
def ax_call_api_page(ax_api_key, org_id, url, params={}, max_retries=2):
    # Validate (or set) Params defaults
    if not params:
        params = {}
    if 'limit' not in params:
        params['limit'] = "500"
    if 'page' not in params:
        params['page'] = "0"
    limit_int = int(params['limit'])
    page_int = int(params['page'])

    full_data_list = []
    while True:
        api_response_package = get_zone_policies(ax_api_key=ax_api_key, org_id=org_id, url=url, params=params, try_count=0, max_retries=max_retries)
        if api_response_package['data']:
            full_data_list.append(api_response_package['data'])
            if len(api_response_package['data']) < limit_int:
                api_response_package['data'] = full_data_list
                return api_response_package
            page_int = page_int + 1
            params['page'] = str(page_int)
        else:
            return api_response_package

# user parameters using argparse
parser = argparse.ArgumentParser()

parser.add_argument(
    'ax_api_key',
    type=str,
    help='Automox API Key.')

parser.add_argument(
    'zone_id',
    type=str,
    help="Legacy ZoneID number where you want to remove policies")

args = parser.parse_args()

ax_api_key = args.ax_api_key
org_id = args.zone_id
url = "https://console.automox.com/api/policies"

#code block to remove each policy in zone
response = ax_call_api_page(ax_api_key, org_id, url, params={}, max_retries=2)
    
policyid = []

for id in response['data'][0]:
    policy_id = id["id"]
    policyid.append(policy_id)

print("deleting policies" + " " + f"{policyid}")
policyid = [str(id) for id in policyid]

for id in policyid:
    
    query = {
    "o": f"{org_id}",
    "page": "0",
    "limit": "500"
    }

    headers = {"Authorization": f"Bearer {ax_api_key}"}

    url = "https://console.automox.com/api/policies/" + id
    response = requests.delete(url, headers=headers, params=query)

    if response.status_code == 204:
        print("success")
    else:
        data = response.json()
        print(data)


