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
def ax_audit_api_call(api_key, org_uuid, date, url, params=None, data=None, try_count=0, max_retries=2):
    retry_statuses = [429, 500, 502, 503, 504]
    retry_wait_timer = 5

    headers = {
    "x-ax-organization-uuid": org_uuid,
    "Authorization": "Bearer " + api_key
  }
  
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code in retry_statuses:
        try_count = try_count + 1
        if try_count <= max_retries:
            time.sleep(retry_wait_timer)
            return ax_audit_api_call(api_key=api_key, org_uuid=org_uuid, date=date, url=url, params=params, try_count=try_count, max_retries=max_retries)
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
def ax_call_api_page(api_key, org_uuid, date, url, params={}, max_retries=2):
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
        api_response_package = ax_audit_api_call(api_key, org_uuid, date, url, params=params, try_count=0, max_retries=max_retries)
        if api_response_package['data']:
            full_data_list.append(api_response_package['data'])
            if len(api_response_package['data']) < limit_int:
                api_response_package['data'] = full_data_list
                return api_response_package
            page_int = page_int + 1
            params['page'] = str(page_int)
        else:
            return api_response_package


def audit_data_response_query(audit_data):
    datalist = []
    rawdata = []

    url = "https://console.automox.com/api/audit-service/v1/orgs/" + org_uuid + "/events"
    
    data = ax_call_api_page(api_key, org_uuid, date, url, params=params, max_retries=2)
    response = json.dumps(data, indent=4)

    for entry in data['data']:
        data = entry['data']
        for response in data:
            id = response['id']
            severity = response['severity']
            timeoffset = response['timezone_offset']
            time = response['time']

            time = time / 1000
            time = datetime.datetime.fromtimestamp(time);
            time = str(time) + "UTC"
    
            try:
                observables = response['observables']
                user = observables[0]['value']
                zone = observables[2]['value']
                policydata = response['web_resources']
                for webdata in policydata:
                    policyid = webdata['uid']
                    policyname = webdata['name']
                    policytype = webdata["type"]
                    url = webdata["url_string"]
                    rawauditdata = response['raw_data']

                datalist.append({'event_id': id, 'user': user, 'zone': zone, 'id': policyid, 'policy_name': policyname, 'url': url, 'event_type': policytype, 'severity': severity, 'time':time, 'time_offset': timeoffset})
                rawdata.append({'data': rawauditdata})

            except: 
                pass
        
        if audit_data == "auditdata":
            return datalist
        if audit_data == "rawdata":
            return rawdata
        else:
            print("Invalid entry. please use either the auditdata or rawdata flags")


# user parameters using argparse
parser = argparse.ArgumentParser()

parser.add_argument(
    'ax_api_key',
    type=str,
    help='Automox API Key.')

parser.add_argument(
    'org_uuid',
    type=str,
    help='Automox Org UUID.')

parser.add_argument(
    'date',
    type=str,
    help='Date of the audited events, format is in YYYY-MM-DD, example: 2024-06-28.')

parser.add_argument(
    'datatype',
    type=str,
    help='Flag to indicate audit data type. Choose either auditdata or rawdata')

# Parse the args into the args variable holder
args = parser.parse_args()

# (Optional) Map the args values into the named variables you are using later
api_key = args.ax_api_key
org_uuid = args.org_uuid
date = args.date
audit_data = args.datatype

params = {
        "date": date,
        "limit": "500"}


newresponse = audit_data_response_query(audit_data)
response = json.dumps(newresponse, indent=4)
# print(response)

print('generating csv file...')

# create csv file
csv_file = f"auditlogs_{date}.csv"

# Get the list of keys (column names) from the first dictionary
try:
  keys = newresponse[0].keys()

  with open(csv_file, 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, fieldnames=keys)
    dict_writer.writeheader()
    dict_writer.writerows(newresponse)

except:
    print("no data was found from this date")








